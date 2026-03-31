# PyTree.ps1 - Karakter Onarılmış Versiyon

# Eğer script'e dışarıdan parametre vermek istersen burayı kullanabilirsin
param()

# Karakter kodlamasını UTF-8'e zorla
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

function Show-PyTree {
    param(
        [string]$Path = ".",
        [string]$Indent = "",
        [string[]]$Exclude = @(".git", "__pycache__", ".vs", "obj", "bin", "venv", ".pytest_cache",".ps1")
    )
    
    # Mevcut klasördeki .py dosyalarını ve (içinde .py barındıran) alt klasörleri al
    $rawItems = Get-ChildItem -Path $Path -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -notin $Exclude -and (
            ($_.Attributes -match "Directory" -and @(Get-ChildItem $_.FullName -Recurse -Filter *.py -File -ErrorAction SilentlyContinue).Count -gt 0) -or 
            ($_.Name -like "*.py")
        )
    }
    $items = $rawItems | Sort-Object Attributes -Descending 

    # Karakter Kodları (UTF-8 destekli konsollarda └── ├── │ karakterlerini düzgün basar)
    $uL = [char]0x2514 + [char]0x2500 + [char]0x2500 + " " # └──
    $uT = [char]0x251C + [char]0x2500 + [char]0x2500 + " " # ├──
    $uV = [char]0x2502 + "   "                         # │

    for ($i = 0; $i -lt $items.Count; $i++) {
        $isLast = $i -eq ($items.Count - 1)
        $connector = if ($isLast) { $uL } else { $uT }
        
        if ($items[$i].Attributes -match "Directory") {
            # Klasör ise sarı renkte yazdır ve içine gir (Recurse)
            Write-Host ($Indent + $connector + $items[$i].Name) -ForegroundColor Yellow
            $branch = if ($isLast) { "    " } else { $uV }
            $newIndent = $Indent + $branch
            Show-PyTree -Path $items[$i].FullName -Indent $newIndent -Exclude $Exclude
        } else {
            # Dosya ise beyaz renkte yazdır
            Write-Host ($Indent + $connector + $items[$i].Name) -ForegroundColor White
        }
    }
}

# Başlat: Mevcut klasör adını en tepeye (Root) ekle
$rootName = Split-Path (Get-Location) -Leaf
Write-Host $rootName -ForegroundColor Cyan
Show-PyTree
Write-Host ""