<#
.SYNOPSIS
    Inicia el ecosistema QFChain + AgenteMamba de forma automática y no interactiva.
.DESCRIPTION
    Este script está diseñado para ser ejecutado como una tarea programada al inicio de sesión.
    Lanza qfchaind y AgenteMamba en segundo plano, valida que los servicios se inicien
    correctamente y realiza el stake si es posible, sin abrir ventanas visibles ni el navegador.
#>

# --- Configuración ---
$sandboxDir = "C:\AGI_Jairo_Sandbox"
$qfchainDir = "$sandboxDir\QFChain-All-in-One\node"
$venvPython = "$sandboxDir\venv\Scripts\python.exe"
$mambaScript = "$sandboxDir\src\agentes\AgenteMamba.py"
$sidecarScript = "$sandboxDir\tccu_sidecar.py"
$validatorAddress = "0x68F9E1D08e410C1d7530813C63E1bce05E8F05Bf"
$stakeAmount = "1000000000000000000000"  # 1000 tokens
$sleepSeconds = 5
$maxRetries = 12
$rpcUrl = "http://localhost:8545"
$logFile = "$sandboxDir\log_inicio_automatico.txt"

# --- Cargar variables de entorno desde .env ---
$envFile = "$sandboxDir\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | Where-Object { $_ -match '=' -and $_ -notmatch '^#' } | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $name = $Matches[1].Trim()
            $value = $Matches[2].Trim()
            [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

# Archivo que contiene las constantes universales
$constantsFile = "$sandboxDir\constantes_universales.txt"
if (-not (Test-Path $constantsFile)) {
    $constantsText = @"
=== CONSTANTES UNIVERSALES FUNDAMENTALES ===
Velocidad de la luz (c)                = 299792458 m/s
Constante de Planck (h)                = 6.62607015e-34 J·s
Constante de Planck reducida (ħ)       = 1.054571817e-34 J·s
Constante gravitacional (G)            = 6.67430e-11 m³/kg/s²
Constante de estructura fina (α)       ≈ 1/137.035999084
Constante de Boltzmann (k)             = 1.380649e-23 J/K
Constante de Stefan-Boltzmann (σ)      = 5.670374419e-8 W/m²/K⁴
Constante de Rydberg (R∞)              = 10973731.568160 m⁻¹
Masa del electrón (me)                 = 9.1093837015e-31 kg
Masa del protón (mp)                   = 1.67262192369e-27 kg
Masa del neutrón (mn)                  = 1.67492749804e-27 kg
Carga elemental (e)                    = 1.602176634e-19 C
Número de Avogadro (NA)                = 6.02214076e23 mol⁻¹
Constante de los gases (R)             = 8.314462618 J/(mol·K)
Constante de Faraday (F)               = 96485.33212 C/mol
Constante de Hubble (H0)               ≈ 67.4 km/s/Mpc
Parámetro de densidad de materia (Ωm)  ≈ 0.315
Parámetro de densidad de energía oscura (ΩΛ) ≈ 0.685
Edad del universo                      ≈ 13.8 Ga
Temperatura de la radiación de fondo   ≈ 2.72548 K
Constante cosmológica (Λ)              ≈ 1.1056e-52 m⁻²
Masa de Planck (mP)                    ≈ 2.176434e-8 kg
Longitud de Planck (lP)                ≈ 1.616255e-35 m
Tiempo de Planck (tP)                  ≈ 5.391247e-44 s
"@
    $constantsText | Out-File -FilePath $constantsFile -Encoding UTF8
}
$hexData = [System.BitConverter]::ToString([System.Text.Encoding]::UTF8.GetBytes((Get-Content -Path $constantsFile -Raw -Encoding UTF8))).Replace("-","").ToLower()
$txDataHex = "0x$hexData"

$toAddress = "0x0000000000000000000000000000000000000001"

# --- Limpieza de log anterior ---
Clear-Content $logFile -ErrorAction SilentlyContinue

# --- Funciones auxiliares (con logging a archivo) ---
function Log-Message {
    param ([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] $Message"
    Add-Content -Path $logFile -Value $logEntry
}

# --- INICIO DE EJECUCIÓN ---
Log-Message "================ INICIO ECOSYSTEMA AUTOMÁTICO ================"

# --- PASO 0: Limpieza de procesos anteriores ---
Log-Message "[0/5] Iniciando limpieza de procesos anteriores..."
# Detener qfchaind
Get-Process qfchaind -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Log-Message "Procesos 'qfchaind' detenidos."
# Detener agentes de python
$mambaProcess = Get-CimInstance Win32_Process -Filter "name = 'python.exe' AND commandLine LIKE '%AgenteMamba.py%'"
if ($mambaProcess) {
    Log-Message "Deteniendo proceso AgenteMamba (PID: $($mambaProcess.ProcessId))."
    Stop-Process -Id $mambaProcess.ProcessId -Force
}
$sidecarProcess = Get-CimInstance Win32_Process -Filter "name = 'python.exe' AND commandLine LIKE '%tccu_sidecar.py%'"
if ($sidecarProcess) {
    Log-Message "Deteniendo proceso tccu_sidecar (PID: $($sidecarProcess.ProcessId))."
    Stop-Process -Id $sidecarProcess.ProcessId -Force
}
Log-Message "Limpieza de procesos completada."


function Wait-ForRpc {
    Log-Message "Esperando a que qfchaind RPC esté disponible..."
    $tryCount = 0
    do {
        try {
            $body = '{"jsonrpc":"2.0","method":"qfchain_getBlockNumber","params":[],"id":1}'
            $response = Invoke-RestMethod -Uri $rpcUrl -Method Post -Body $body -ContentType "application/json" -ErrorAction Stop
            if ($null -ne $response.result) {
                Log-Message "✅ Nodo RPC listo. Bloque actual: $($response.result)"
                return $true
            }
        } catch {}
        $tryCount++
        Log-Message "   Reintentando ($tryCount/$maxRetries)..."
        Start-Sleep -Seconds $sleepSeconds
    } while ($tryCount -lt $maxRetries)
    Log-Message "❌ No se pudo conectar con qfchaind después de $maxRetries intentos."
    return $false
}

function Get-Balance {
    param([string]$address)
    $body = @{ jsonrpc="2.0"; method="qfchain_getBalance"; params=@($address); id=1 } | ConvertTo-Json
    try {
        $response = Invoke-RestMethod -Uri $rpcUrl -Method Post -Body $body -ContentType "application/json"
        if ($null -ne $response.result) {
            $balanceStr = $response.result
            if ($balanceStr -like "0x*") {
                return [System.Numerics.BigInteger]::Parse($balanceStr.Substring(2), [System.Globalization.NumberStyles]::HexNumber)
            } else {
                return [System.Numerics.BigInteger]::Parse($balanceStr)
            }
        }
    } catch {
        Log-Message "Error al obtener balance: $_"
    }
    return $null
}

function Invoke-Stake {
    param([string]$address, [string]$amount)
    $qfcli = "$qfchainDir\bin\qfcli.exe"
    Log-Message "Enviando stake de $amount a $address..."
    $result = & $qfcli stake $address "$amount" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Log-Message "✅ Stake realizado con éxito."
        return $true
    } else {
        Log-Message "❌ Error en stake: $result"
        return $false
    }
}

function Get-Nonce {
    param([string]$address)
    $body = @{ jsonrpc="2.0"; method="qfchain_getNonce"; params=@($address); id=1 } | ConvertTo-Json
    try {
        $response = Invoke-RestMethod -Uri $rpcUrl -Method Post -Body $body -ContentType "application/json"
        if ($null -ne $response.result) {
            $nonceStr = $response.result
            if ($nonceStr -like "0x*") {
                return [Convert]::ToInt64($nonceStr, 16)
            } else {
                return [int64]$nonceStr
            }
        }
    } catch {
        Log-Message "Error al obtener nonce: $_"
    }
    return $null
}

function Send-Transaction {
    param([string]$from, [string]$to, [bigint]$value, [string]$data, [int64]$nonce)

    $valueHex = if ($value -eq 0) { "0x0" } else { "0x$([Convert]::ToString($value, 16))" }
    $nonceHex = "0x$([Convert]::ToString($nonce, 16))"
    $gasHex = "0x200000" # Convertir gas a hex
    $gasPriceHex = "0x3B9ACA00" # Convertir gasPrice a hex

    $body = @{
        jsonrpc = "2.0"
        method = "qfchain_sendTransaction"
        params = @(
            $from,
            $to,
            $valueHex,
            $gasHex,
            $gasPriceHex,
            $data,
            $nonceHex
        )
        id = 1
    } | ConvertTo-Json -Depth 3

    Log-Message "Payload de transacción: $body" # Añadido para depuración

    try {
        $response = Invoke-RestMethod -Uri $rpcUrl -Method Post -Body $body -ContentType "application/json"
        if ($null -ne $response.result) {
            Log-Message "✅ Transacción enviada: $($response.result)" # Log más claro
            return $response.result
        } else {
            $errMsg = $response.error.message # Captura el mensaje de error del nodo
            Log-Message "❌ Error del nodo: $errMsg"
            return $null
        }
    } catch {
        Log-Message "❌ Excepción HTTP: $_" # Log de excepciones HTTP
        return $null
    }
}

# --- PASO 1: Iniciar QFChaind ---
Log-Message "[1/5] Iniciando QFChaind de forma visible..."
$env:STAKING_ADDRESS = $validatorAddress
$qfchaindCommand = "Write-Host '=== INICIANDO NODO QFCHAIND ==='; & '$qfchainDir\bin\qfchaind.exe' start"
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $qfchaindCommand -WorkingDirectory $qfchainDir
Log-Message "Comando para iniciar QFChaind enviado."

# --- PASO 2: Esperar RPC y gestionar Stake ---
if (-not (Wait-ForRpc)) {
    Log-Message "Abortando inicio. QFChaind no respondió."
    exit 1
}

Log-Message "[2/5] Verificando saldo del validador..."
$balance = Get-Balance -address $validatorAddress
if ($null -eq $balance) {
    Log-Message "❌ No se pudo obtener el saldo de $validatorAddress."
} else {
    Log-Message "Saldo actual: $balance wei."
    $stakeAmountNum = [bigint]$stakeAmount
    if ($balance -ge $stakeAmountNum) {
        Invoke-Stake -address $validatorAddress -amount $stakeAmountNum
    } else {
        Log-Message "⚠️ Saldo insuficiente ($balance < $stakeAmountNum). No se realiza stake."
    }
}

# --- PASO 3: Enviar transacción de prueba (inscripción de constantes) ---
Log-Message "[3/5] Enviando transacción de prueba a $toAddress..."
$nonce = Get-Nonce $validatorAddress
if ($nonce -ne $null) {
    $txHash = Send-Transaction -from $validatorAddress -to $toAddress -value 0 -data $txDataHex -nonce $nonce
    if ($txHash) {
        Log-Message "✅ Transacción enviada: $txHash"
    } else {
        Log-Message "⚠️ No se pudo enviar la transacción."
    }
}
else {
    Log-Message "❌ No se pudo obtener el nonce para enviar la transacción."
}

# --- PASO 4: Iniciar Sidecar TCCU ---
Log-Message "[4/5] Iniciando sidecar TCCU de forma visible..."
$sidecarCommand = "Write-Host '=== INICIANDO SIDECAR TCCU ==='; & '$venvPython' -u '$sidecarScript'"
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $sidecarCommand
Log-Message "Comando para iniciar sidecar enviado."
Start-Sleep -Seconds 3 # Pequeña pausa para dar tiempo al sidecar a iniciarse

# --- PASO 5: Iniciar AgenteMamba ---
Log-Message "[5/5] Iniciando AgenteMamba de forma visible..."
$agentCommand = "Write-Host '=== INICIANDO AGENTE MAMBA ==='; & '$venvPython' -u '$mambaScript'"
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $agentCommand
Log-Message "Comando para iniciar AgenteMamba enviado."


Log-Message "✅ Ecosistema iniciado en modo automático."
Log-Message "============================================================"
