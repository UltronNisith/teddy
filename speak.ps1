# Teddy v3.1 - Windows NATURAL voice speaker (WinRT / OneCore voices)
# These voices (George, Ryan, Sonia...) sound far less robotic than the
# old SAPI "Desktop" voices pyttsx3 can see, and they include British males.
# Text arrives via the TEDDY_SAY environment variable (no quoting problems).
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Media.SpeechSynthesis, ContentType = WindowsRuntime]
$synth = New-Object Windows.Media.SpeechSynthesis.SpeechSynthesizer
$voices = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices
Write-Output ("Natural voices found: " + (($voices | ForEach-Object { $_.DisplayName + " (" + $_.Language + ", " + $_.Gender + ")" }) -join ", "))
$pick = $voices | Where-Object { $_.Gender -eq 'Male' -and $_.Language -eq 'en-GB' } | Select-Object -First 1
if (-not $pick) { $pick = $voices | Where-Object { $_.Language -eq 'en-GB' } | Select-Object -First 1 }
if (-not $pick) { $pick = $voices | Where-Object { $_.Gender -eq 'Male' } | Select-Object -First 1 }
if ($pick) { $synth.Voice = $pick; Write-Output ("Using natural voice: " + $pick.DisplayName) }
$text = $env:TEDDY_SAY
if ($text) {
  $op = $synth.SpeakTextAsync($text)
  # wait for the async speech to finish
  $task = [System.WindowsRuntimeSystemExtensions]::AsTask($op)
  $task.Wait()
}
