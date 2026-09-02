param(
  [string]$Svg = ".\figure\study-design.svg",
  [string]$Out = ".\_render.png",
  [int]$Dpi = 300
)
# Rasterise an SVG with headless Edge at a chosen DPI. The SVG is inlined into a
# throwaway page sized in raw pixels, so no device-scale-factor guesswork is needed.
$ErrorActionPreference = "Stop"
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$svgPath = (Resolve-Path $Svg).Path
$text = Get-Content $svgPath -Raw -Encoding UTF8

$wMm = [double]([regex]::Match($text, 'width="([\d.]+)mm"').Groups[1].Value)
$hMm = [double]([regex]::Match($text, 'height="([\d.]+)mm"').Groups[1].Value)
$wPx = [int][math]::Round($wMm / 25.4 * $Dpi)
$hPx = [int][math]::Round($hMm / 25.4 * $Dpi)

$inline = $text -replace '(?s)^\s*<\?xml.*?\?>', ''
$inline = [regex]::Replace($inline, '(<svg\b[^>]*?)\swidth="[\d.]+mm"', '$1')
$inline = [regex]::Replace($inline, '(<svg\b[^>]*?)\sheight="[\d.]+mm"', '$1')
$inline = [regex]::Replace($inline, '<svg\b', "<svg width=`"$wPx`" height=`"$hPx`"", 1)

$html = @"
<!doctype html><meta charset="utf-8">
<style>html,body{margin:0;padding:0;background:#fff;overflow:hidden}
svg{display:block}</style>
$inline
"@
$tmpHtml = Join-Path $env:TEMP ("svgshot_" + [guid]::NewGuid().ToString("N") + ".html")
$profile = Join-Path $env:TEMP ("edgeshot_" + [guid]::NewGuid().ToString("N"))
[IO.File]::WriteAllText($tmpHtml, $html, [Text.UTF8Encoding]::new($false))

$outFull = [IO.Path]::GetFullPath((Join-Path (Get-Location) $Out))
$cliArgs = @(
  "--headless", "--disable-gpu", "--no-first-run", "--hide-scrollbars",
  "--user-data-dir=$profile", "--force-device-scale-factor=1",
  "--window-size=$wPx,$hPx", "--screenshot=$outFull",
  ("file:///" + ($tmpHtml -replace '\\', '/'))
)
& $edge @cliArgs 2>&1 | Out-Null

Remove-Item $tmpHtml -Force -ErrorAction SilentlyContinue
Remove-Item $profile -Recurse -Force -ErrorAction SilentlyContinue

Add-Type -AssemblyName System.Drawing
$img = [Drawing.Image]::FromFile($outFull)
$got = "{0}x{1}" -f $img.Width, $img.Height
$img.Dispose()
"{0} -> {1} px (want {2}x{3}) | {4} x {5} mm @ {6} dpi" -f $Out, $got, $wPx, $hPx, $wMm, $hMm, $Dpi
