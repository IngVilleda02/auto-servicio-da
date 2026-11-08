<#
  Prepara una foto para el sitio: crea versiones de 480, 800 y 1200 px de ancho en img/.

  Uso (desde la carpeta sitio):
    powershell -ExecutionPolicy Bypass -File tools\nueva-foto.ps1 -Origen "C:\ruta\foto.jpg" -Nombre "pintura-defensa"

  Después agrega { "nombre": "pintura-defensa", "alt": "..." } a la "galeria" del servicio en data\config.json
  y ejecuta: py build.py
#>
param(
  [Parameter(Mandatory = $true)][string]$Origen,
  [Parameter(Mandatory = $true)][ValidatePattern('^[a-z0-9-]+$')][string]$Nombre,
  [int]$Calidad = 78
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$destino = Join-Path $PSScriptRoot '..\img'
$img = [System.Drawing.Image]::FromFile((Resolve-Path $Origen))
try {
  # Respeta la orientación EXIF de fotos de celular
  if ($img.PropertyIdList -contains 274) {
    switch ([BitConverter]::ToUInt16($img.GetPropertyItem(274).Value, 0)) {
      3 { $img.RotateFlip('Rotate180FlipNone') }
      6 { $img.RotateFlip('Rotate90FlipNone') }
      8 { $img.RotateFlip('Rotate270FlipNone') }
    }
  }
  $enc = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
  $ep = New-Object System.Drawing.Imaging.EncoderParameters(1)
  $ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [int64]$Calidad)

  $anchos = @(480, 800, 1200) | Where-Object { $_ -le $img.Width }
  if (-not $anchos) { $anchos = @($img.Width) }
  foreach ($w in $anchos) {
    $h = [int][math]::Round($img.Height * $w / $img.Width)
    $bmp = New-Object System.Drawing.Bitmap $w, $h
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.Clear([System.Drawing.Color]::White)
    $g.InterpolationMode = 'HighQualityBicubic'; $g.PixelOffsetMode = 'HighQuality'; $g.SmoothingMode = 'HighQuality'
    $g.DrawImage($img, 0, 0, $w, $h); $g.Dispose()
    $archivo = Join-Path $destino "$Nombre-$w.jpg"
    $bmp.Save($archivo, $enc, $ep); $bmp.Dispose()
    "{0}  {1}x{2}  {3} KB" -f (Split-Path $archivo -Leaf), $w, $h, [int]((Get-Item $archivo).Length / 1KB)
  }
} finally { $img.Dispose() }
