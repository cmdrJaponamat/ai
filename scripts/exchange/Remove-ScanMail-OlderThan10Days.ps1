param(
    [ValidateSet('Estimate', 'Delete')]
    [string]$Mode = 'Estimate'
)

$ErrorActionPreference = 'Stop'
$root = 'C:\ProgramData\Aurora\Exchange'
$logDir = Join-Path $root 'Logs'
New-Item -Path $logDir -ItemType Directory -Force | Out-Null
$logFile = Join-Path $logDir ('scan-purge-{0:yyyyMMdd}.jsonl' -f (Get-Date))
$mutex = New-Object System.Threading.Mutex($false, 'Global\AuroraExchangeScanMail10DayPurge')

function Write-Event {
    param([string]$Event, [object]$Data)
    $record = [ordered]@{ Time = (Get-Date).ToString('o'); Event = $Event; Data = $Data }
    $record | ConvertTo-Json -Depth 5 -Compress | Add-Content -Path $logFile -Encoding UTF8
}

$locked = $false
try {
    if (-not $mutex.WaitOne(0)) { throw 'Another scan mail purge run is active.' }
    $locked = $true
    Add-PSSnapin Microsoft.Exchange.Management.PowerShell.SnapIn -ErrorAction Stop

    $scan = Get-Mailbox -Identity 'scan' -ErrorAction Stop
    $expected = @('scan@aurora-logistics.ru', 'scan@aurora-line.com')
    $actual = @($scan.EmailAddresses | ForEach-Object { $_.ToString().ToLowerInvariant() })
    foreach ($address in $expected) {
        if ($actual -notcontains ('smtp:' + $address)) { throw "Sender address missing: $address" }
    }

    # KQL's received filter uses a date, not a time. The previous ten full
    # calendar days are retained; today's messages are retained too.
    $cutoff = (Get-Date).Date.AddDays(-10).ToString('MM/dd/yyyy', [Globalization.CultureInfo]::InvariantCulture)
    $query = '(from:scan@aurora-logistics.ru OR from:scan@aurora-line.com) AND kind:email AND received<' + $cutoff
    Write-Event 'start' @{ Mode = $Mode; Query = $query }

    if ($Mode -eq 'Delete') {
        $now = Get-Date
        $badBackups = @(Get-MailboxDatabase -Status -ErrorAction Stop | Where-Object {
            (-not $_.LastFullBackup) -or (($now - [datetime]$_.LastFullBackup).TotalHours -gt 24)
        } | ForEach-Object { $_.Name })
        if ($badBackups.Count -gt 0) {
            throw ('Full backup missing or older than 24 hours for: ' + ($badBackups -join ', '))
        }
        Write-Event 'backup-check-passed' @{ DatabaseCount = @(Get-MailboxDatabase -Status).Count }
    }

    $mailboxes = @(Get-Mailbox -ResultSize Unlimited -ErrorAction Stop | Where-Object {
        $_.Guid -ne $scan.Guid
    })
    $matches = New-Object System.Collections.Generic.List[object]
    [long]$totalCount = 0
    [long]$totalBytes = 0
    $index = 0
    foreach ($mailbox in $mailboxes) {
        $index++
        $estimate = Search-Mailbox -Identity $mailbox.Identity -SearchQuery $query -EstimateResultOnly -ErrorAction Stop
        if (-not $estimate.Success) { throw "Estimate failed for $($mailbox.Alias)" }
        $count = [long]$estimate.ResultItemsCount
        if ($count -ge 10000) { throw "Search limit reached for $($mailbox.Alias): $count" }
        if ($count -gt 0) {
            $bytes = [long]$estimate.ResultItemsSize.ToBytes()
            $totalCount += $count
            $totalBytes += $bytes
            $matches.Add([pscustomobject]@{ Identity = $mailbox.Identity; Alias = $mailbox.Alias; Count = $count; Bytes = $bytes })
            Write-Event 'estimate-mailbox' @{ Alias = $mailbox.Alias; Count = $count; Bytes = $bytes }
        }
        if (($index % 25) -eq 0) { Write-Event 'progress' @{ Checked = $index; Total = $mailboxes.Count } }
    }
    Write-Event 'estimate-complete' @{ Mailboxes = $mailboxes.Count; MatchingMailboxes = $matches.Count; Items = $totalCount; Bytes = $totalBytes }

    if ($totalCount -gt 50000 -or $totalBytes -gt 75161927680) {
        throw "Safety threshold exceeded: $totalCount items, $totalBytes bytes"
    }

    if ($Mode -eq 'Delete') {
        foreach ($match in $matches) {
            $result = Search-Mailbox -Identity $match.Identity -SearchQuery $query -DeleteContent -Force -Confirm:$false -ErrorAction Stop
            if (-not $result.Success) { throw "Delete failed for $($match.Alias)" }
            Write-Event 'delete-mailbox' @{ Alias = $match.Alias; EstimatedItems = $match.Count; DeletedItems = [long]$result.ResultItemsCount }
        }
        Write-Event 'delete-complete' @{ MatchingMailboxes = $matches.Count; EstimatedItems = $totalCount; EstimatedBytes = $totalBytes }
    }
    [pscustomobject]@{ Mode = $Mode; Query = $query; Mailboxes = $mailboxes.Count; MatchingMailboxes = $matches.Count; Items = $totalCount; Bytes = $totalBytes; Log = $logFile } | ConvertTo-Json -Compress
}
catch {
    Write-Event 'error' @{ Message = $_.Exception.Message; Stack = $_.ScriptStackTrace }
    Write-Error $_
    exit 1
}
finally {
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
