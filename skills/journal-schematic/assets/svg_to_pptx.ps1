param(
    [Parameter(Mandatory = $true)][string]$Svg,
    [Parameter(Mandatory = $true)][string]$Out,
    [string]$Proof,
    [int]$ProofDpi = 200
)

# PowerPoint is the only SVG-to-shape converter on this machine, and also the
# most faithful one available anywhere: it reads the SVG itself and emits native
# DrawingML, so type stays type (real Arial runs, not outlines) and the fills
# stay editable. Inkscape and LibreOffice are not installed here.
#
# Two quirks drive the shape of this script:
#   * an imported SVG lands as msoGraphic (28), and Shape.Ungroup() refuses it
#     with "This member can only be accessed for a group" - the conversion is
#     only reachable through the ribbon command ObjectsUngroup, which in turn
#     needs a real UI selection in an active window;
#   * the enums are supplied as raw values because the Office interop assembly
#     is not loaded in PowerShell 7.

$ErrorActionPreference = "Stop"
$svgPath = (Resolve-Path $Svg).Path
$outPath = [IO.Path]::GetFullPath((Join-Path (Get-Location) $Out))
New-Item -ItemType Directory -Force -Path (Split-Path $outPath) | Out-Null
if (Test-Path $outPath) { Remove-Item $outPath -Force }

# the slide is sized to the figure, so the deck exports back at true print size
$head = (Get-Content $svgPath -TotalCount 3) -join " "
if ($head -notmatch 'width="([\d.]+)mm"\s+height="([\d.]+)mm"') {
    throw "could not read mm dimensions from $svgPath"
}
$wPt = [double]$Matches[1] * 72 / 25.4
$hPt = [double]$Matches[2] * 72 / 25.4

# Two things have to be pre-compensated, because PowerPoint's SVG importer gets
# them wrong and there is no way to correct them after the fact:
#   * font-size is read as a raw pixel value while geometry is scaled by the
#     viewBox->canvas factor, so type arrives 25% small inside full-size artwork;
#   * the text box is placed as if the baseline sat 1.207 em below the box top,
#     but PowerPoint then draws it at ~0.973 em, lifting every line by 0.2335 em
#     - measured at 600 dpi against the browser render, and visible as the drawn
#     >= glyph sinking below its own sentence.
# Both are applied to a throwaway copy; the print SVG is left untouched.
$raw = [IO.File]::ReadAllText($svgPath)
if ($raw -notmatch 'viewBox="0 0 ([\d.]+) ') { throw "could not read viewBox from $svgPath" }
$k = ($wPt / 72 * 96) / [double]$Matches[1]
$baselineEm = 0.2335
$fixed = [regex]::Replace($raw, '<text ([^>]*)>', {
        param($m)
        $at = $m.Groups[1].Value
        if ($at -match 'font-size="([\d.]+)"') {
            $sz = [double]$Matches[1]
            $at = $at -replace 'font-size="[\d.]+"', ('font-size="' + [math]::Round($sz * $k, 4) + '"')
            if ($at -match '\sy="(-?[\d.]+)"') {
                $y = [double]$Matches[1] + $sz * $baselineEm
                $at = $at -replace '\sy="-?[\d.]+"', (' y="' + [math]::Round($y, 3) + '"')
            }
        }
        '<text ' + $at + '>'
    })
$srcPath = [IO.Path]::Combine([IO.Path]::GetTempPath(), "ppt_" + [IO.Path]::GetFileName($svgPath))
[IO.File]::WriteAllText($srcPath, $fixed)

$app = New-Object -ComObject PowerPoint.Application
$app.Visible = -1
$pres = $app.Presentations.Add(-1)
try {
    $pres.PageSetup.SlideWidth = $wPt
    $pres.PageSetup.SlideHeight = $hPt
    # PowerPoint silently clamps a slide to its minimum dimension (1 inch), and
    # then everything is quietly laid out at the wrong scale. Catch it here
    # rather than discovering it in the proof.
    if ([math]::Abs($pres.PageSetup.SlideWidth - $wPt) -gt 1.0 -or
        [math]::Abs($pres.PageSetup.SlideHeight - $hPt) -gt 1.0) {
        throw ("PowerPoint clamped the slide to {0:N2} x {1:N2} pt (asked for {2:N2} x {3:N2}); " +
            "the figure is smaller than the 1 inch minimum in one dimension") -f `
            $pres.PageSetup.SlideWidth, $pres.PageSetup.SlideHeight, $wPt, $hPt
    }
    $slide = $pres.Slides.Add(1, 12)            # ppLayoutBlank

    $pic = $slide.Shapes.AddPicture($srcPath, 0, -1, 0, 0, $wPt, $hPt)
    if ($pic.Type -ne 28) {
        throw "PowerPoint imported the file as type $($pic.Type), not a vector graphic (28)"
    }

    $app.ActiveWindow.Activate()
    $app.ActiveWindow.View.GotoSlide(1)
    $pic.Select()
    if (-not $app.CommandBars.GetEnabledMso("ObjectsUngroup")) {
        throw "Convert to Shape is unavailable for this graphic"
    }
    $app.CommandBars.ExecuteMso("ObjectsUngroup")
    Start-Sleep -Milliseconds 1500

    # re-group so the figure stays one object on the slide; double-clicking
    # still steps inside to edit an individual shape
    $names = @($slide.Shapes | ForEach-Object { $_.Name })
    if ($names.Count -lt 2) { throw "conversion produced $($names.Count) shape(s)" }
    # deliberately not resized: PowerPoint gives every converted text box a
    # 7.2 pt inset, so the group's bounding box overhangs the artwork. Forcing
    # it back to the slide size would shrink the geometry without shrinking the
    # font sizes, and the type would come out too wide for its layout.
    $g = $slide.Shapes.Range($names).Group()
    $g.Name = [IO.Path]::GetFileNameWithoutExtension($outPath)

    $script:leaves = 0; $script:texts = 0
    function Walk($items) {
        foreach ($s in $items) {
            if ($s.Type -eq 6) { Walk $s.GroupItems }        # msoGroup
            else {
                $script:leaves++
                if ($s.HasTextFrame -eq -1 -and $s.TextFrame.HasText -eq -1) { $script:texts++ }
            }
        }
    }
    Walk $g.GroupItems
    "$([IO.Path]::GetFileName($outPath)): $script:leaves shapes, $script:texts live text boxes, $([math]::Round($wPt/72*25.4,1)) x $([math]::Round($hPt/72*25.4,1)) mm"

    $pres.SaveAs($outPath, 24)                  # ppSaveAsOpenXMLPresentation
    if ($Proof) {
        $proofPath = [IO.Path]::GetFullPath((Join-Path (Get-Location) $Proof))
        New-Item -ItemType Directory -Force -Path (Split-Path $proofPath) | Out-Null
        $slide.Export($proofPath, "PNG", [int]($wPt / 72 * $ProofDpi), [int]($hPt / 72 * $ProofDpi))
    }
}
finally {
    $pres.Saved = -1
    $pres.Close()
    $app.Quit()
    [Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
    Remove-Item $srcPath -Force -ErrorAction SilentlyContinue
}
