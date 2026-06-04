$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$projectRoot = Split-Path -Parent $PSScriptRoot
$brandingDir = Join-Path $projectRoot "assets\branding"
New-Item -ItemType Directory -Force -Path $brandingDir | Out-Null

function New-RoundedRectPath {
  param(
    [System.Drawing.RectangleF]$Rect,
    [float]$Radius
  )

  $path = New-Object System.Drawing.Drawing2D.GraphicsPath
  $diameter = $Radius * 2

  $path.AddArc($Rect.X, $Rect.Y, $diameter, $diameter, 180, 90)
  $path.AddArc($Rect.Right - $diameter, $Rect.Y, $diameter, $diameter, 270, 90)
  $path.AddArc($Rect.Right - $diameter, $Rect.Bottom - $diameter, $diameter, $diameter, 0, 90)
  $path.AddArc($Rect.X, $Rect.Bottom - $diameter, $diameter, $diameter, 90, 90)
  $path.CloseFigure()
  return $path
}

function New-Color {
  param(
    [int]$A,
    [int]$R,
    [int]$G,
    [int]$B
  )

  return [System.Drawing.Color]::FromArgb($A, $R, $G, $B)
}

function New-Brush {
  param(
    [System.Drawing.RectangleF]$Rect,
    [System.Drawing.Color]$StartColor,
    [System.Drawing.Color]$EndColor,
    [float]$Angle
  )

  return New-Object System.Drawing.Drawing2D.LinearGradientBrush($Rect, $StartColor, $EndColor, $Angle)
}

function New-BaseIconBitmap {
  $bitmap = New-Object System.Drawing.Bitmap 1024, 1024, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
  $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
  $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
  $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
  $graphics.Clear([System.Drawing.Color]::Transparent)

  $tileRect = New-Object System.Drawing.RectangleF 70, 70, 884, 884
  $tilePath = New-RoundedRectPath -Rect $tileRect -Radius 220
  $tileBrush = New-Brush -Rect $tileRect -StartColor (New-Color 255 8 22 38) -EndColor (New-Color 255 22 63 114) -Angle 45
  $graphics.FillPath($tileBrush, $tilePath)

  $glowRect = New-Object System.Drawing.RectangleF 120, 120, 784, 784
  $glowPath = New-RoundedRectPath -Rect $glowRect -Radius 190
  $glowBrush = New-Brush -Rect $glowRect -StartColor (New-Color 60 112 214 255) -EndColor (New-Color 0 112 214 255) -Angle 90
  $graphics.FillPath($glowBrush, $glowPath)

  $tilePen = New-Object System.Drawing.Pen (New-Color 110 141 219 255), 12
  $graphics.DrawPath($tilePen, $tilePath)

  $screenRect = New-Object System.Drawing.RectangleF 210, 300, 604, 374
  $screenPath = New-RoundedRectPath -Rect $screenRect -Radius 84
  $screenBrush = New-Brush -Rect $screenRect -StartColor (New-Color 255 9 18 31) -EndColor (New-Color 255 18 44 78) -Angle 90
  $graphics.FillPath($screenBrush, $screenPath)
  $screenPen = New-Object System.Drawing.Pen (New-Color 255 115 211 248), 18
  $graphics.DrawPath($screenPen, $screenPath)

  $shineRect = New-Object System.Drawing.RectangleF 255, 330, 320, 110
  $shinePath = New-RoundedRectPath -Rect $shineRect -Radius 50
  $shineBrush = New-Brush -Rect $shineRect -StartColor (New-Color 85 255 255 255) -EndColor (New-Color 0 255 255 255) -Angle 120
  $graphics.FillPath($shineBrush, $shinePath)

  $playBrush = New-Object System.Drawing.SolidBrush (New-Color 255 240 138 36)
  $playPoints = @(
    (New-Object System.Drawing.PointF 455, 398),
    (New-Object System.Drawing.PointF 455, 576),
    (New-Object System.Drawing.PointF 620, 487)
  )
  $graphics.FillPolygon($playBrush, $playPoints)

  $dotBrush = New-Object System.Drawing.SolidBrush (New-Color 255 255 178 92)
  $graphics.FillEllipse($dotBrush, 695, 357, 42, 42)

  $antennaPen = New-Object System.Drawing.Pen (New-Color 255 212 232 246), 18
  $antennaPen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
  $antennaPen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
  $graphics.DrawLine($antennaPen, 418, 285, 340, 160)
  $graphics.DrawLine($antennaPen, 606, 285, 684, 160)

  $signalPen = New-Object System.Drawing.Pen (New-Color 210 95 214 242), 18
  $signalPen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
  $signalPen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
  $graphics.DrawArc($signalPen, 625, 130, 120, 120, 225, 90)
  $graphics.DrawArc($signalPen, 590, 95, 190, 190, 225, 90)

  $basePen = New-Object System.Drawing.Pen (New-Color 255 212 232 246), 22
  $basePen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
  $basePen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
  $graphics.DrawLine($basePen, 432, 690, 592, 690)
  $graphics.DrawLine($basePen, 512, 690, 512, 780)
  $graphics.DrawLine($basePen, 430, 780, 594, 780)

  $graphics.Dispose()
  return $bitmap
}

function Resize-Bitmap {
  param(
    [System.Drawing.Bitmap]$SourceBitmap,
    [int]$Width,
    [int]$Height
  )

  $resized = New-Object System.Drawing.Bitmap $Width, $Height, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $graphics = [System.Drawing.Graphics]::FromImage($resized)
  $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
  $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
  $graphics.Clear([System.Drawing.Color]::Transparent)
  $graphics.DrawImage($SourceBitmap, 0, 0, $Width, $Height)
  $graphics.Dispose()
  return $resized
}

function Save-PngBytes {
  param(
    [System.Drawing.Bitmap]$Bitmap
  )

  $stream = New-Object System.IO.MemoryStream
  $Bitmap.Save($stream, [System.Drawing.Imaging.ImageFormat]::Png)
  $bytes = $stream.ToArray()
  $stream.Dispose()
  return $bytes
}

function Save-Ico {
  param(
    [System.Drawing.Bitmap]$BaseBitmap,
    [string]$OutputPath
  )

  $sizes = @(16, 24, 32, 48, 64, 128, 256)
  $images = @()
  foreach ($size in $sizes) {
    $resized = Resize-Bitmap -SourceBitmap $BaseBitmap -Width $size -Height $size
    $images += [PSCustomObject]@{
      Size = $size
      Bytes = [byte[]](Save-PngBytes -Bitmap $resized)
    }
    $resized.Dispose()
  }

  $fileStream = [System.IO.File]::Open($OutputPath, [System.IO.FileMode]::Create)
  $writer = New-Object System.IO.BinaryWriter($fileStream)
  $writer.Write([UInt16]0)
  $writer.Write([UInt16]1)
  $writer.Write([UInt16]$images.Count)

  $offset = 6 + (16 * $images.Count)
  foreach ($image in $images) {
    $dimension = if ($image.Size -ge 256) { 0 } else { $image.Size }
    $writer.Write([byte]$dimension)
    $writer.Write([byte]$dimension)
    $writer.Write([byte]0)
    $writer.Write([byte]0)
    $writer.Write([UInt16]1)
    $writer.Write([UInt16]32)
    $writer.Write([UInt32]$image.Bytes.Length)
    $writer.Write([UInt32]$offset)
    $offset += $image.Bytes.Length
  }

  foreach ($image in $images) {
    $writer.Write([byte[]]$image.Bytes)
  }

  $writer.Flush()
  $writer.Dispose()
  $fileStream.Dispose()
}

function New-InstallerBanner {
  param(
    [System.Drawing.Bitmap]$IconBitmap,
    [string]$OutputPath
  )

  $bitmap = New-Object System.Drawing.Bitmap 404, 772, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
  $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
  $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
  $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit

  $bgRect = New-Object System.Drawing.RectangleF 0, 0, 404, 772
  $bgBrush = New-Brush -Rect $bgRect -StartColor (New-Color 255 8 20 36) -EndColor (New-Color 255 17 57 104) -Angle 90
  $graphics.FillRectangle($bgBrush, $bgRect)

  $bandBrush = New-Brush -Rect (New-Object System.Drawing.RectangleF 0, 0, 404, 772) -StartColor (New-Color 110 53 170 224) -EndColor (New-Color 0 53 170 224) -Angle 35
  $graphics.FillPie($bandBrush, -140, 420, 520, 420, 0, 180)
  $graphics.FillRectangle((New-Object System.Drawing.SolidBrush (New-Color 20 255 255 255)), 0, 0, 404, 772)

  $icon = Resize-Bitmap -SourceBitmap $IconBitmap -Width 176 -Height 176
  $graphics.DrawImage($icon, 114, 76, 176, 176)
  $icon.Dispose()

  $titleFont = New-Object System.Drawing.Font "Segoe UI Semibold", 22, ([System.Drawing.FontStyle]::Bold)
  $subtitleFont = New-Object System.Drawing.Font "Segoe UI", 11, ([System.Drawing.FontStyle]::Regular)
  $kickerFont = New-Object System.Drawing.Font "Segoe UI", 10, ([System.Drawing.FontStyle]::Bold)
  $whiteBrush = New-Object System.Drawing.SolidBrush (New-Color 255 245 248 252)
  $softBrush = New-Object System.Drawing.SolidBrush (New-Color 255 188 221 245)
  $accentBrush = New-Object System.Drawing.SolidBrush (New-Color 255 255 190 120)

  $graphics.DrawString("ADABTECH", $kickerFont, $accentBrush, 120, 280)
  $graphics.DrawString("Adamsy Free TV", $titleFont, $whiteBrush, 58, 312)
  $graphics.DrawString("Live channels with a simple desktop experience.", $subtitleFont, $softBrush, (New-Object System.Drawing.RectangleF 58, 378, 288, 80))

  $cardRect = New-Object System.Drawing.RectangleF 44, 510, 316, 150
  $cardPath = New-RoundedRectPath -Rect $cardRect -Radius 28
  $cardBrush = New-Brush -Rect $cardRect -StartColor (New-Color 80 255 255 255) -EndColor (New-Color 18 255 255 255) -Angle 90
  $graphics.FillPath($cardBrush, $cardPath)
  $cardPen = New-Object System.Drawing.Pen (New-Color 70 164 225 255), 2
  $graphics.DrawPath($cardPen, $cardPath)

  $graphics.DrawString("Free-to-air streams", $kickerFont, $whiteBrush, 68, 538)
  $graphics.DrawString("Fast launcher`nSimple channel list`nDesktop shortcut support", $subtitleFont, $softBrush, (New-Object System.Drawing.RectangleF 68, 578, 240, 70))

  $bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
  $graphics.Dispose()
  $bitmap.Dispose()
}

function New-InstallerSmallImage {
  param(
    [System.Drawing.Bitmap]$IconBitmap,
    [string]$OutputPath
  )

  $bitmap = New-Object System.Drawing.Bitmap 138, 138, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
  $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
  $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality

  $bgRect = New-Object System.Drawing.RectangleF 0, 0, 138, 138
  $bgPath = New-RoundedRectPath -Rect $bgRect -Radius 28
  $bgBrush = New-Brush -Rect $bgRect -StartColor (New-Color 255 11 28 48) -EndColor (New-Color 255 18 73 128) -Angle 45
  $graphics.FillPath($bgBrush, $bgPath)
  $bgPen = New-Object System.Drawing.Pen (New-Color 100 157 226 255), 2
  $graphics.DrawPath($bgPen, $bgPath)

  $icon = Resize-Bitmap -SourceBitmap $IconBitmap -Width 94 -Height 94
  $graphics.DrawImage($icon, 22, 22, 94, 94)
  $icon.Dispose()

  $bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
  $graphics.Dispose()
  $bitmap.Dispose()
}

$iconBitmap = New-BaseIconBitmap
$iconPngPath = Join-Path $brandingDir "adamsy-free-tv-icon-1024.png"
$iconIcoPath = Join-Path $brandingDir "adamsy-free-tv.ico"
$wizardImagePath = Join-Path $brandingDir "adamsy-free-tv-wizard.png"
$wizardSmallPath = Join-Path $brandingDir "adamsy-free-tv-wizard-small.png"

$iconBitmap.Save($iconPngPath, [System.Drawing.Imaging.ImageFormat]::Png)
Save-Ico -BaseBitmap $iconBitmap -OutputPath $iconIcoPath
New-InstallerBanner -IconBitmap $iconBitmap -OutputPath $wizardImagePath
New-InstallerSmallImage -IconBitmap $iconBitmap -OutputPath $wizardSmallPath
$iconBitmap.Dispose()

Write-Host "Branding assets generated:"
Write-Host "  $iconIcoPath"
Write-Host "  $iconPngPath"
Write-Host "  $wizardImagePath"
Write-Host "  $wizardSmallPath"
