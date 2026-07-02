$endpoints = @(
    @{ path="/health"; method="GET" },
    @{ path="/api/system"; method="GET" },
    @{ path="/api/chat"; method="POST"; body='{"message":"ping"}' },
    @{ path="/api/chat/stream"; method="POST"; body='{"message":"ping"}' },
    @{ path="/api/memory"; method="GET" },
    @{ path="/api/history"; method="GET" },
    @{ path="/api/automation"; method="POST"; body='{"goal":"ping", "steps":[], "expected_output":"ping"}' },
    @{ path="/api/browser"; method="POST"; body='{"action":"ping"}' },
    @{ path="/api/voice"; method="POST"; body='{"action":"ping"}' }
)

foreach ($ep in $endpoints) {
    try {
        if ($ep.method -eq "GET") {
            $r = Invoke-WebRequest -Uri "http://localhost:8000$($ep.path)" -Method GET -UseBasicParsing -ErrorAction Stop
        } else {
            $r = Invoke-WebRequest -Uri "http://localhost:8000$($ep.path)" -Method POST -Body $ep.body -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
        }
        Write-Host "PASS: $($ep.path)"
    } catch {
        if ($_.Exception.Response) {
            $status = $_.Exception.Response.StatusCode.value__
            $msg = $_.Exception.Message
            $stream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($stream)
            $body = $reader.ReadToEnd()
            Write-Host "FAIL: $($ep.path) - $status $msg - Body: $body"
        } else {
            Write-Host "FAIL: $($ep.path) - $($_.Exception.Message)"
        }
    }
}
