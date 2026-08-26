# ============================================================================
# arranque_unificado.ps1 - ARRANQUE UNIFICADO DEL ORGANISMO AGI JAIRO
# AutoClaw 2026-08-26 - Un solo comando levanta TODOS los servicios vivos.
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File arranque_unificado.ps1
#       (arranca lo que falta en ventanas separadas)
#   ... -Tunnel     (ademas abre el tunel publico cloudflared)
#   ... -Ecosistema (ejecuta iniciar_ecosistema_auto.ps1: limpieza + qfchaind
#                    con stake + TX constantes + sidecar + mamba)
#   ... -Chequear   (solo muestra el estado actual, no arranca nada)
#   ... -Parar      (detiene todos los servicios del organismo)
# ============================================================================
param(
    [switch]$Tunnel,
    [switch]$Ecosistema,
    [switch]$Parar,
    [switch]$Chequear
)
$ErrorActionPreference = 'Continue'
$WS = "C:\Users\Jairo Omar\AGI_Workspace"
$SB = "C:\AGI_Jairo_Sandbox"
$PY = "python"
$SB_PY = "$SB\venv\Scripts\python.exe"
$QF_EXE = "$SB\QFChain-All-in-One\node\bin\qfchaind.exe"
$QF_DIR = "$SB\QFChain-All-in-One\node\bin"
$MAMBA_SCRIPT = "$SB\src\agentes\AgenteMamba.py"
$SIDECAR_SCRIPT = "$SB\tccu_sidecar.py"
$AUTO_SCRIPT = "$SB\archive\iniciar_ecosistema_auto.ps1"
$CLOUDFLARED = "C:\Program Files (x86)\cloudflared\cloudflared.exe"

# --- Cargar variables del .env al proceso (necesarias para mamba/sidecar) ---
$envFile = "$SB\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | Where-Object { $_ -match '=' -and $_ -notmatch '^#' } | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $name = $Matches[1].Trim()
            $value = $Matches[2].Trim()
            [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

$SERVICIOS = @(
    @{ nombre = "qfchain6d_rpc";       puerto = 8545; exe = $QF_EXE; args = @("start");                    dir = $QF_DIR;  py = $null },
    @{ nombre = "enlace_codex";        puerto = 8787; exe = $PY;    args = @("enlace_codex.py");            dir = $WS; py = $PY },
    @{ nombre = "bridge_tccu";         puerto = 8006; exe = $PY;    args = @("tccu_engine\bridge_tccu.py"); dir = $WS; py = $PY },
    @{ nombre = "sidecar_v2";          puerto = 8004; exe = $SB_PY; args = @("-u", $SIDECAR_SCRIPT);       dir = $SB; py = $SB_PY },
    @{ nombre = "agente_mamba_v2";     puerto = 8001; exe = $SB_PY; args = @("-u", $MAMBA_SCRIPT);         dir = $SB; py = $SB_PY },
    @{ nombre = "dashboard_monitoreo"; puerto = 8050; exe = $PY;    args = @("dashboard_monitoreo_final.py"); dir = $WS; py = $PY },
    @{ nombre = "qswift_terminal";     puerto = 8051; exe = $PY;    args = @("qswift_servidor_local.py");     dir = $WS; py = $PY },
    @{ nombre = "vigilante_organismo"; puerto = 0;    exe = $PY;    args = @("vigilante_organismo.py");       dir = $WS; py = $PY }
)

function Test-Puerto([int]$puerto) {
    if ($puerto -le 0) { return $false }
    try {
        $c = New-Object Net.Sockets.TcpClient
        $iar = $c.BeginConnect("127.0.0.1", $puerto, $null, $null)
        $ok = $iar.AsyncWaitHandle.WaitOne(900)
        if ($ok -and $c.Connected) { $c.Close(); return $true }
        $c.Close(); return $false
    } catch { return $false }
}

function Estado-Actual {
    Write-Output ""
    Write-Output "  ESTADO ACTUAL DEL ORGANISMO:"
    foreach ($s in $SERVICIOS) {
        if ($s.puerto -gt 0) {
            $st = if (Test-Puerto $s.puerto) { "ACTIVO" } else { "caido" }
            Write-Output ("  {0,-24} :{1,-6} {2}" -f $s.nombre, $s.puerto, $st)
        }
    }
    $t = Test-Puerto 8051
    if ($t) {
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:8051/network_status" -UseBasicParsing -TimeoutSec 5
            Write-Output ("  qswift_api               :" + $r.Content)
        } catch { }
    }
}

if ($Chequear) { Estado-Actual; exit 0 }

if ($Ecosistema) {
    Write-Output "  [ECOSISTEMA] Ejecutando iniciar_ecosistema_auto.ps1 (limpieza + qfchaind + stake + sidecar + mamba)..."
    if (Test-Path $AUTO_SCRIPT) {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $AUTO_SCRIPT
        Write-Output "  [ECOSISTEMA] Script de arranque automatico ejecutado. Log: $SB\log_inicio_automatico.txt"
        exit 0
    } else {
        Write-Output "  !! No encontrado: $AUTO_SCRIPT"
    }
}

if ($Parar) {
    Write-Output "  DETENIENDO ORGANISMO..."
    $pids = @()
    foreach ($s in $SERVICIOS) {
        if ($s.puerto -gt 0) {
            $conn = Get-NetTCPConnection -LocalPort $s.puerto -State Listen -ErrorAction SilentlyContinue
            foreach ($c in $conn) { $pids += $c.OwningProcess }
        }
    }
    Get-Process -Name qfchaind, cloudflared -ErrorAction SilentlyContinue | ForEach-Object { $pids += $_.Id }
    $pids = $pids | Sort-Object -Unique
    foreach ($pId in $pids) { Stop-Process -Id $pId -Force -ErrorAction SilentlyContinue; Write-Output ("  detenido PID " + $pId) }
    Write-Output "  ORGANISMO DETENIDO."
    exit 0
}

Write-Output "=========================================================="
Write-Output "  ARRANQUE UNIFICADO - ORGANISMO AGI JAIRO v2.0"
Write-Output "=========================================================="
foreach ($s in $SERVICIOS) {
    if ($s.puerto -gt 0 -and (Test-Puerto $s.puerto)) {
        Write-Output ("  [YA ACTIVO] {0} (:{1})" -f $s.nombre, $s.puerto)
        continue
    }
    Write-Output ("  [ARRANCANDO] {0} ..." -f $s.nombre)
    try {
        if ($s.exe -eq $QF_EXE) {
            Start-Process -FilePath $s.exe -WorkingDirectory $s.dir
        } elseif ($s.puerto -eq 0) {
            Start-Process -FilePath $s.py -ArgumentList $s.args -WorkingDirectory $s.dir -WindowStyle Hidden
        } else {
            Start-Process -FilePath $s.exe -ArgumentList $s.args -WorkingDirectory $s.dir
        }
    } catch {
        Write-Output ("    !! error: " + $_.Exception.Message)
    }
}

if ($Tunnel) {
    Write-Output "  [ARRANCANDO] tunel publico cloudflared ..."
    try {
        Start-Process -FilePath $CLOUDFLARED -ArgumentList @("tunnel", "--url", "http://127.0.0.1:8051", "--no-autoupdate") -WorkingDirectory $WS
    } catch { Write-Output "    !! cloudflared no encontrado" }
}

Write-Output ""
Write-Output "  Esperando 30 s para verificacion (mamba tarda ~30 s en enlazar)..."
Start-Sleep -Seconds 30
Estado-Actual
Write-Output ""
Write-Output "  ORGANISMO ARRANCADO. Ventanas separadas por servicio."
Write-Output "  (Q-SWIFT publico: lee la URL https://...trycloudflare.com del tunel)"
