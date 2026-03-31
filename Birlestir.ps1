param(
    [double]$Minutes = 100, 
    [string]$Path = ".",   
    [string[]]$Exclude = @("\.git", "\.vs", "\\obj\\", "\\bin\\", "\.pyc", "\.exe", "\.dll", "\.png", "\.jpg", "\.ps1", "\.ps1xml", "\.pytest_cache", "\.csv") 
)

# Karakter kodlamasını UTF-8'e zorla
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Pano kütüphanesini yükle
Add-Type -AssemblyName System.Windows.Forms

# Karakterleri Hex olarak tanımla (Kaçış hatasını önlemek için)
# Gerçek "İ" ve "Ş" kullanarak tam Unicode tanımlama:
$islemText = [char]0x0130 + [char]0x015E + "LEM TAMAM"  # İŞLEM TAMAM
$isleniyorText = [char]0x0130 + [char]0x015E + "LEN" + [char]0x0130 + "YOR" # İŞLENİYOR

$threshold = (Get-Date).AddMinutes(-$Minutes)
$combinedContent = New-Object System.Text.StringBuilder
$currentFolder = Split-Path (Get-Location) -Leaf
$separator = "`n`n############################`n`n"

Write-Host "--- Son $Minutes dakikadaki degisimler taraniyor ($Path) ---" -ForegroundColor Cyan

$files = Get-ChildItem -Path $Path -Recurse -File | Where-Object {
    $_.LastWriteTime -gt $threshold -and 
    $_.FullName -notmatch ($Exclude -join "|")
}

if ($files.Count -eq 0) {
    Write-Host "Degisen dosya bulunamadi." -ForegroundColor Yellow
    exit
}

foreach ($file in $files) {
    try {
        $relativeName = Join-Path $currentFolder (Resolve-Path $file.FullName -Relative).Replace(".\", "")
        
        # Hata veren kısım: Değişken ismini ${} ile izole ettik
        Write-Host "${isleniyorText}: $relativeName" -ForegroundColor Green
        
        [void]$combinedContent.Append("--- DOSYA ADI: $relativeName ---`n")
        
        $text = Get-Content -Path $file.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        [void]$combinedContent.Append($text)
        [void]$combinedContent.Append($separator)
    }
    catch {
        Write-Warning "Hata: $($file.Name)"
    }
}

$finalResult = $combinedContent.ToString()

if ($finalResult.Length -gt 0) {
    # Panoya kopyala
    [Windows.Forms.Clipboard]::SetText($finalResult)
    
    Write-Host "`n" + ("=" * 40) -ForegroundColor Green
    # Hata veren kısım: Değişken ismini ${} ile izole ettik
    Write-Host "${islemText}: $($files.Count) DOSYA KOPYALANDI" -ForegroundColor Green
    Write-Host ("=" * 40) + "`n"
}