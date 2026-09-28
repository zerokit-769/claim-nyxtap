<?php
error_reporting(0);
date_default_timezone_set("Asia/Jakarta");

const HOST        = "https://ourcoincash.xyz";
const ORIGIN_HOST = "ourcoincash.xyz";
const ORIGIN_IP   = "107.161.168.10";
const SOLVER_IN   = "https://api.waryono.my.id/in.php";
const SOLVER_OUT  = "https://api.waryono.my.id/res.php";
const SITEKEY     = "QYsWzsX9XGwe1as9FOUzEOzHm2weLwz6bRH8UraH";
const CONFIG_FILE = __DIR__ . "/config.json";
const DATA_DIR    = __DIR__ . "/Data";
const CLAIM_DELAY = 5;
const MAX_PTC_PASS  = 3;
const MAX_PTC_RETRY = 3;

const DEF_UA = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36";

const RST = "\033[0m"; const BOLD = "\033[1m";
const RED = "\033[1;31m"; const GRN = "\033[1;32m";
const YEL = "\033[1;33m"; const CYN = "\033[1;36m";
const WHT = "\033[1;37m";

function is_tty(): bool {
    return function_exists('posix_isatty') && @posix_isatty(STDIN) && @posix_isatty(STDOUT);
}

function prompt(string $label): string {
    echo $label;
    flush();
    $line = fgets(STDIN);
    if ($line === false) {
        fwrite(STDERR, "\nSTDIN bukan terminal interaktif. Jalankan: php our.php\n");
        exit(1);
    }
    return trim($line);
}

function tty_ok_or_die(): void {
    if (is_tty()) return;
}

function clip(string $s): string {
    return is_tty() ? $s : preg_replace('/\033\[[0-9;]*m/', '', $s);
}

function logg(string $type, string $text): void {
    $t = date('H:i:s');
    $tag = $col = '';
    switch ($type) {
        case 's': $tag = 'SUCCESS'; $col = GRN; break;
        case 'e': $tag = 'ERROR';   $col = RED; break;
        case 'w': $tag = 'WARN';    $col = YEL; break;
        default:  $tag = 'INFO';    $col = CYN; break;
    }
    echo clip("{$col}[{$t}] - {$col}[{$tag}] " . RST . WHT . "$text" . RST . "\n");
    flush();
}

function mask_email(?string $email): string {
    if (!$email || strpos($email, '@') === false) return $email ?: '(kosong)';
    [$u, $d] = explode('@', $email, 2);
    $len = strlen($u);
    $u = $len <= 4 ? substr($u, 0, 1) . '****' : substr($u, 0, 2) . '****' . substr($u, -2);
    return "$u@$d";
}

function cookie_file(): string {
    global $CFG;
    if (!is_dir(DATA_DIR)) mkdir(DATA_DIR, 0777, true);
    $email = $CFG['email'] ?? '';
    $h = substr(md5(strtolower(trim($email))), 0, 16);
    return DATA_DIR . "/cookies_{$h}.txt";
}

function curl_req(string $url, array $headers = [], $post = 0): string {
    $ch = curl_init();
    $opts = [
        CURLOPT_URL            => $url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_SSL_VERIFYHOST => false,
        CURLOPT_CONNECTTIMEOUT => 30,
        CURLOPT_TIMEOUT        => 60,
        CURLOPT_COOKIEFILE     => cookie_file(),
        CURLOPT_COOKIEJAR      => cookie_file(),
        CURLOPT_RESOLVE        => [ORIGIN_HOST . ":443:" . ORIGIN_IP],
    ];
    $h = ['User-Agent: ' . DEF_UA, 'Accept: */*'];
    if ($headers) $h = array_merge($h, $headers);
    $opts[CURLOPT_HTTPHEADER] = $h;

    if ($post) {
        $opts[CURLOPT_POST] = true;
        $opts[CURLOPT_POSTFIELDS] = is_array($post) ? http_build_query($post) : $post;
    }

    curl_setopt_array($ch, $opts);
    $body = curl_exec($ch);
    return $body === false ? '' : $body;
}

function solve_adslab(string $label = "[CAPTCHA]") {
    global $CFG;
    $apiKey = trim($CFG['apikey'] ?? '');
    if (!$apiKey) { logg('e', "[SOLVER] API key kosong"); return null; }

    $payload = json_encode([
        'apikey'  => $apiKey,
        'methods' => 'adslab',
        'domain'  => HOST,
        'sitekey' => SITEKEY,
        'subid'   => 'widget_user',
        'json'    => '1',
    ]);

    $ch = curl_init(SOLVER_IN);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
        CURLOPT_POSTFIELDS     => $payload,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_CONNECTTIMEOUT => 20,
        CURLOPT_TIMEOUT        => 40,
    ]);
    $raw = curl_exec($ch);
    $task = json_decode($raw, true);

    if (!is_array($task)) {
        logg('e', "[SOLVER] Respon bukan JSON: " . substr((string)$raw, 0, 200));
        return null;
    }
    $id = trim((string)($task['request'] ?? ''));
    if (!$id) {
        logg('e', "[SOLVER] Gagal submit: " . substr(json_encode($task), 0, 200));
        return null;
    }
    $start = time();
    $poll_no = 0;
    $spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
    $tty = is_tty();

    while (time() - $start < 180) {
        $poll_no++;
        $api = SOLVER_OUT . '?' . http_build_query([
            'apikey' => $apiKey, 'action' => 'get', 'id' => $id, 'json' => '1',
        ]);

        if ($tty) {
            $anim_until = microtime(true) + 2;
            $sp = -1;
            while (microtime(true) < $anim_until) {
                $sp = ($sp + 1) % count($spinner);
                $el = time() - $start;
                printf("\r\033[K%s %s solving %02d:%02d task#%s poll#%d %d/180s",
                    $spinner[$sp], $label, intdiv($el, 60), $el % 60, $id, $poll_no, $el);
                flush();
                usleep(100000);
            }
        } else {
            sleep(2);
        }

        $ch = curl_init($api);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_CONNECTTIMEOUT => 20,
            CURLOPT_TIMEOUT        => 40,
        ]);
        $res = json_decode(curl_exec($ch), true);
        if (!is_array($res)) continue;
        $req = trim((string)($res['request'] ?? ''));
        if ($req === 'CAPCHA_NOT_READY') continue;
        if ($req === '') continue;
        if (strpos($req, 'ERROR_') === 0) {
            if ($tty) echo "\r\033[K";
            logg('e', "[SOLVER] Poll error: $req");
            return null;
        }
        if ($tty) echo "\r\033[K";
        return $req;
    }
    if ($tty) echo "\r\033[K";
    logg('e', "[SOLVER] Timeout polling task $id");
    return null;
}

// ── ANTIBOT (auto-detect: kalau gaada ablinks, skip & tetep jalan) ──
function parse_ablinks(string $html): array {
    $start = strpos($html, 'var ablinks=');
    if ($start === false) $start = strpos($html, 'var ablinks =');
    if ($start === false) return [];
    $eq = strpos($html, '=', $start);
    if ($eq === false) return [];
    $arrStart = $eq + 1;
    while ($arrStart < strlen($html) && ($html[$arrStart] === ' ' || $html[$arrStart] === "\t")) $arrStart++;
    if (!isset($html[$arrStart]) || $html[$arrStart] !== '[') return [];
    $arrEnd = strpos($html, ']', $arrStart);
    if ($arrEnd === false) return [];
    $raw = substr($html, $arrStart, $arrEnd - $arrStart + 1);
    $items = @json_decode($raw, true);
    if (!is_array($items)) return [];
    $out = [];
    foreach ($items as $item) {
        if (!is_string($item)) continue;
        if (preg_match('/rel="(\d+)"/', $item, $rm) && preg_match('/data:image\/[^;]+;base64,([A-Za-z0-9+\/=]+)/', $item, $im)) {
            $out[] = ['rel' => $rm[1], 'b64' => $im[1]];
        }
    }
    return $out;
}

function extract_main_ablink(string $html): ?string {
    if (preg_match('/class="alert\s+alert-warning[^"]*"[^>]*>(.*?)<\/p>/is', $html, $m)) {
        if (preg_match('/data:image\/[^;]+;base64,([A-Za-z0-9+\/=]+)/', $m[1], $im)) {
            return $im[1];
        }
    }
    return null;
}

function antibot_submit(string $mainB64, array $ablinks) {
    global $CFG;
    $apiKey = trim($CFG['apikey'] ?? '');
    if (!$apiKey) return ['ok' => false, 'msg' => 'no apikey'];
    $payload = [
        'apikey'  => $apiKey,
        'methods' => 'antibot',
        'main'    => $mainB64,
        'json'    => 1,
    ];
    foreach ($ablinks as $a) {
        $payload[(string)$a['rel']] = $a['b64'];
    }
    $ch = curl_init(SOLVER_IN);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
        CURLOPT_POSTFIELDS     => json_encode($payload),
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_CONNECTTIMEOUT => 20,
        CURLOPT_TIMEOUT        => 60,
    ]);
    $r = json_decode(curl_exec($ch), true);
    if (!is_array($r)) return ['ok' => false, 'msg' => 'submit not json', 'raw' => (string)curl_error($ch)];
    if (isset($r['status']) && $r['status'] == 1 && !empty($r['request'])) {
        return ['ok' => true, 'id' => $r['request']];
    }
    return ['ok' => false, 'msg' => $r['request'] ?? 'submit failed', 'raw' => json_encode($r)];
}

function antibot_poll(string $id) {
    global $CFG;
    $apiKey = trim($CFG['apikey'] ?? '');
    for ($i = 0; $i < 80; $i++) {
        sleep(3);
        $url = SOLVER_OUT . '?' . http_build_query([
            'apikey' => $apiKey, 'action' => 'get', 'id' => $id, 'json' => 1,
        ]);
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_CONNECTTIMEOUT => 20,
            CURLOPT_TIMEOUT        => 40,
        ]);
        $raw = curl_exec($ch);
        $j = json_decode($raw, true);
        if (stripos((string)$raw, 'OK|') === 0) {
            $tok = trim(substr((string)$raw, 3));
            if ($tok) return ['status' => 'ready', 'token' => $tok];
        }
        if (!is_array($j)) continue;
        if (isset($j['status']) && $j['status'] == 1 && !empty($j['request'])) {
            return ['status' => 'ready', 'token' => $j['request']];
        }
        $rv = $j['request'] ?? '';
        if ($rv === 'CAPCHA_NOT_READY') continue;
        return ['status' => 'error', 'msg' => $rv ?: 'unknown'];
    }
    return ['status' => 'error', 'msg' => 'timeout'];
}

function map_antibot_result(string $token, array $ablinks): ?array {
    $ids = preg_split('/[\s,]+/', trim($token));
    $ids = array_values(array_filter($ids, 'strlen'));
    if (empty($ids)) return null;
    $relIds = array_map(fn($a) => (string)$a['rel'], $ablinks);
    $n = count($relIds);
    $allRel = true;
    foreach ($ids as $t) if (!in_array((string)$t, $relIds, true)) { $allRel = false; break; }
    if ($allRel) return $ids;
    $allInt = true;
    foreach ($ids as $t) if (!preg_match('/^\d+$/', (string)$t)) { $allInt = false; break; }
    if ($allInt) {
        $intIds = array_map('intval', $ids);
        $min = min($intIds); $max = max($intIds);
        if ($min >= 0 && $max <= $n - 1) {
            $mapped = [];
            foreach ($intIds as $i) if (isset($relIds[$i])) $mapped[] = $relIds[$i];
            if (count($mapped) == count($intIds)) return $mapped;
        }
        if ($min >= 1 && $max <= $n) {
            $mapped = [];
            foreach ($intIds as $i) if (isset($relIds[$i - 1])) $mapped[] = $relIds[$i - 1];
            if (count($mapped) == count($intIds)) return $mapped;
        }
    }
    return $ids;
}

function solve_antibot(string $html): ?string {
    $ablinks = parse_ablinks($html);
    if (empty($ablinks)) return null;  // auto-detect: gaada → skip
    $mainB64 = extract_main_ablink($html);
    if (!$mainB64) return null;
    $tty = is_tty();

    $s = antibot_submit($mainB64, $ablinks);
    if (!$s['ok']) {
        logg('e', "[ANTIBOT] submit gagal: " . ($s['msg'] ?? '?'));
        return null;
    }

    $start = time();
    $spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
    $sp = 0;
    $poll_no = 0;
    while (true) {
        $poll_no++;
        if ($tty) {
            $el = time() - $start;
            printf("\r\033[K%s [ANTIBOT] %d links | solving %02d:%02d task#%s poll#%d",
                $spinner[$sp % count($spinner)], count($ablinks), intdiv($el, 60), $el % 60, $s['id'], $poll_no);
            flush();
            $sp++;
        }
        $r = antibot_poll($s['id']);
        if ($r['status'] !== 'ready') {
            if ($tty) { echo "\r\033[K"; }
            logg('e', "[ANTIBOT] poll gagal: " . ($r['msg'] ?? '?'));
            return null;
        }
        break;
    }
    $mapped = map_antibot_result($r['token'], $ablinks);
    if (!$mapped) {
        if ($tty) echo "\r\033[K";
        logg('e', "[ANTIBOT] map hasil gagal");
        return null;
    }
    if ($tty) echo "\r\033[K";
    return implode(' ', $mapped);
}

function is_claim_success(string $body): ?string {
    $msg = null;
    if (stripos($body, 'Good job') !== false || stripos($body, 'has been added') !== false) {
        if (preg_match('/text:\s*\'([^\']+)\'/i', $body, $m)) $msg = trim($m[1]);
        elseif (preg_match('/<p[^>]*class="text-success"[^>]*>(.*?)<\/p>/is', $body, $m)) $msg = trim(strip_tags($m[1]));
        if (!$msg) $msg = 'Claim success';
        return $msg;
    }
    if (preg_match('/<div[^>]*class="alert\s+alert-danger[^"]*"[^>]*>(.*?)<\/div>/is', $body, $m)) {
        return trim(strip_tags($m[1]));
    }
    return null;
}

function x(string $a, string $b, string $s, int $n = 1): string {
    $parts = explode($a, $s);
    if (!isset($parts[$n])) return '';
    $out = explode($b, $parts[$n])[0];
    return trim($out);
}

function parse_csrf(string $html): string {
    $pats = [
        '/name="csrf_token_name"\s+id="[^"]*"\s+value="([^"]+)"/i',
        '/name="csrf_token_name"\s+value="([^"]+)"/i',
        "/name='csrf_token_name'\s+value='([^']+)'/i",
        '/name="csrf_token_name"[^>]*value="([^"]+)"/i',
    ];
    foreach ($pats as $p) {
        if (preg_match($p, $html, $m)) return $m[1];
    }
    return '';
}

function parse_token(string $html): string {
    if (preg_match('/name="token"\s+value="([^"]+)"/i', $html, $m)) return $m[1];
    return '';
}

function parse_balance(string $html) {
    if (preg_match('/class="acc-amount"[^>]*>\s*<i[^>]*><\/i>\s*([\d,\.]+)/i', $html, $m)) {
        return (float)str_replace(',', '', $m[1]);
    }
    if (preg_match('/Balance.*?([\d,]{4,}\.\d{2})/s', $html, $m)) {
        return (float)str_replace(',', '', $m[1]);
    }
    return null;
}

function parse_faucet_status(string $html): array {
    $status = 'UNKNOWN';
    if (preg_match('/<h4 class="lh-1 mb-1">\s*([A-Z]+)\s*<\/h4>/', $html, $m)) $status = trim($m[1]);
    $reward = null;
    if (preg_match('/id="faucetRewardValue">\s*([\d,\.]+)\s*</', $html, $m)) $reward = $m[1];
    $claims_left = null;
    if (preg_match('/([\d,]+)\/[\d,]+\s*<\/h4>\s*<h6[^>]*>claims left/i', $html, $m)) $claims_left = $m[1];
    return ['status' => $status, 'reward' => $reward, 'claims_left' => $claims_left];
}

function get_cooldown_minutes(string $html): int {
    if (preg_match('/<h4 class="lh-1 mb-1">(\d+)<\/h4>\s*<h6 class="mb-0">minutes/i', $html, $m)) {
        return (int)$m[1] * 60;
    }
    return 0;
}

function is_logged_in(string $html): bool {
    return stripos($html, 'Logout') !== false;
}

function looks_like_login_page(string $html): bool {
    return strpos($html, 'name="password"') !== false
        && strpos($html, 'name="email"') !== false
        && stripos($html, 'Logout') === false;
}

function is_ptc_success(string $resp): ?string {
    if (stripos($resp, 'Good job') !== false || stripos($resp, 'coins has been added') !== false) {
        if (preg_match('/text:\s*\'([^\']+)\'/i', $resp, $m)) return trim($m[1]);
        if (preg_match('/<p[^>]*class="text-success"[^>]*>(.*?)<\/p>/is', $resp, $m)) return trim(strip_tags($m[1]));
        if (preg_match('/<div[^>]*class="alert\s+alert-success[^"]*"[^>]*>(.*?)<\/div>/is', $resp, $m)) return trim(strip_tags($m[1]));
        return 'PTC Claim success';
    }
    return null;
}

function parse_ptc_ads(string $html): array {
    $ads = [];
    $parts = preg_split('/<div class="col-sm-6 mb-3">/', $html);
    if (!is_array($parts)) return $ads;
    array_shift($parts);
    foreach ($parts as $part) {
        $chunk = substr($part, 0, 3000);
        if (!preg_match('/href="(?:https:\/\/ourcoincash\.xyz)?\/ptc\/view\/(\d+)"/', $chunk, $m)) continue;
        $ad_id = $m[1];
        $title = "Ad #$ad_id";
        if (preg_match('/<h5[^>]*class="card-title[^"]*"[^>]*>\s*(.*?)\s*<\/h5>/s', $chunk, $tm)) {
            $title = trim(preg_replace('/\s+/', ' ', $tm[1]));
        }
        $reward = '?';
        if (preg_match('/([\d,\.]+)\s*coins/', $chunk, $rm)) $reward = $rm[1];
        $dur = 5;
        if (preg_match('/<\/i>\s*(\d+)\s*s\b/', $chunk, $dm)) $dur = (int)$dm[1];
        $ads[] = ['id' => $ad_id, 'title' => $title, 'reward' => $reward, 'duration' => $dur];
    }
    return $ads;
}

function timer(int $seconds, string $label = "Countdown"): void {
    $a = time() + $seconds;
    while (true) {
        $b = $a - time();
        if ($b < 1) break;
        echo "\r$label " . sprintf('%02d:%02d', intdiv($b, 60), $b % 60) . "   ";
        flush();
        sleep(1);
    }
    echo "\r" . str_repeat(' ', 50) . "\r";
}

function b() {
    $r = curl_req(HOST . '/dashboard');
    return parse_balance($r);
}

function do_login(): int {
    global $CFG;
    $email = $CFG['email'];
    logg('i', "Starting Login: " . mask_email($email));

    $r = curl_req(HOST . '/login');
    if ($r === '') { logg('e', "[LOGIN] Response kosong"); return 0; }
    $csrf = parse_csrf($r);
    if (!$csrf) { logg('e', "[LOGIN] CSRF tidak ketemu, len=" . strlen($r)); return 0; }
    logg('i', "CSRF OK, minta token solver...");

    $tok = solve_adslab("[LOGIN]");
    if (!$tok) { logg('e', "[LOGIN] Token kosong"); return 0; }

    $resp = curl_req(HOST . '/auth/login', [
        'Content-Type: application/x-www-form-urlencoded',
        'Referer: ' . HOST . '/login',
        'Origin: ' . HOST,
    ], [
        'csrf_token_name'    => $csrf,
        'email'              => $email,
        'password'           => $CFG['password'],
        'captcha'            => 'adslabpro',
        'alcaptcha-response' => $tok,
    ]);

    if (is_logged_in($resp)) {
        logg('s', "Login Completed!");
        return 1;
    }
    logg('e', "[LOGIN] Gagal, len=" . strlen($resp));
    return 0;
}

function ensure_login(): bool {
    $dash = curl_req(HOST . '/dashboard');
    if (is_logged_in($dash)) return true;
    return do_login() === 1;
}

function run_faucet() {
    $old_bal = null;
    while (true) {
        $r = curl_req(HOST . '/faucet');
        if (!is_logged_in($r)) { logg('e', "[FAUCET] Session expired"); return -1; }

        $info = parse_faucet_status($r);
        if ($info['status'] !== 'UNKNOWN') {
            logg('i', "[FAUCET] status: {$info['status']} | reward: {$info['reward']} | claims left: {$info['claims_left']}");
        }

        if ($info['status'] !== 'READY') {
            $cd = get_cooldown_minutes($r);
            if ($cd > 0) {
                logg('w', "Cooldown " . sprintf('%02d:%02d', intdiv($cd, 60), $cd % 60));
                timer($cd, "Waiting");
                continue;
            }
            sleep(5);
            continue;
        }

        $csrf  = parse_csrf($r);
        $token = parse_token($r);
        if (!$csrf || !$token) { sleep(3); continue; }

        $antibotStr = '';
        $hasAB = strpos($r, 'var ablinks=') !== false || strpos($r, 'var ablinks =') !== false;
        if ($hasAB) {
            $ab = solve_antibot($r);
            if ($ab === null) { sleep(3); continue; }
            $antibotStr = ' ' . $ab;
        }

        $before_bal = b();
        if ($before_bal === null) $before_bal = 0.0;

        $cap = solve_adslab("[FAUCET]");
        if (!$cap) { sleep(3); continue; }

        $payload = [
            'csrf_token_name'    => $csrf,
            'token'              => $token,
            'captcha'            => 'adslabpro',
            'alcaptcha-response' => $cap,
        ];
        if ($antibotStr !== '') {
            $payload['antibotlinks'] = trim($antibotStr);
        }

        $v = curl_req(HOST . '/faucet/verify', [
            'Content-Type: application/x-www-form-urlencoded',
            'Referer: ' . HOST . '/faucet',
            'Origin: ' . HOST,
        ], $payload);

        $claimMsg = is_claim_success($v);
        if ($claimMsg !== null && stripos($v, 'alert-danger') === false) {
            $new_bal = b();
            $diff = null;
            if ($new_bal !== null) $diff = $new_bal - $before_bal;
            logg('s', "$claimMsg | balance: " .
                ($new_bal !== null ? number_format($new_bal, 2) . " coins" : "?"));
            timer(CLAIM_DELAY, "Jeda");
            $cd = get_cooldown_minutes($v);
            if ($cd > 0) {
                logg('w', "Cooldown " . sprintf('%02d:%02d', intdiv($cd, 60), $cd % 60));
                timer($cd, "Waiting");
            }
            continue;
        }
        if ($claimMsg !== null && stripos($v, 'alert-danger') !== false) {
            logg('e', "[FAUCET] server: $claimMsg");
        }
        if (is_logged_in($v)) {
            logg('e', "[FAUCET] session hilang setelah verify");
            return -1;
        }

        $cd2 = get_cooldown_minutes($v);
        if ($cd2 > 0) {
            logg('w', "Cooldown " . sprintf('%02d:%02d', intdiv($cd2, 60), $cd2 % 60));
            timer($cd2, "Waiting");
        } else {
            logg('w', "[FAUCET] verify gagal, retry 5s");
            sleep(5);
        }
    }
}

function claim_one_ad(array $ad, float $current_balance): array {
    $id = $ad['id']; $dur = $ad['duration'];
    $view = curl_req(HOST . '/ptc/view/' . $id);
    if (looks_like_login_page($view)) return [null, $current_balance];
    $csrf  = parse_csrf($view);
    $token = parse_token($view);
    if (!$csrf || !$token) { logg('w', "[PTC] csrf/token gak ada di view #$id"); return [false, $current_balance]; }

    if ($dur > 0) timer($dur, "[PTC] View");

    $cap = solve_adslab("[PTC]");
    if (!$cap) return [false, $current_balance];

    $v = curl_req(HOST . '/ptc/verify/' . $id, [
        'Content-Type: application/x-www-form-urlencoded',
        'Referer: ' . HOST . '/ptc/view/' . $id,
        'Origin: ' . HOST,
    ], [
        'captcha'            => 'adslabpro',
        'csrf_token_name'    => $csrf,
        'token'              => $token,
        'alcaptcha-response' => $cap,
    ]);

    if (looks_like_login_page($v)) return [null, $current_balance];
    $ptcMsg = is_ptc_success($v);
    if ($ptcMsg !== null) {
        $new_bal = b();
        if ($new_bal !== null) $current_balance = $new_bal;
        logg('s', "$ptcMsg | balance: " .
            ($new_bal !== null ? number_format($new_bal, 2) . " coins" : "?"));
        return [true, $current_balance];
    }
    return [false, $current_balance];
}

function run_ptc() {
    $claimed = [];
    $current_balance = null;
    for ($pass = 1; $pass <= MAX_PTC_PASS; $pass++) {
        $r = curl_req(HOST . '/ptc');
        if (!is_logged_in($r)) { logg('e', "[PTC] Session expired"); return -1; }

        $all = parse_ptc_ads($r);
        $pending = array_filter($all, function ($a) use ($claimed) {
            return !in_array($a['id'], $claimed);
        });

        if ($pass === 1) logg('i', "[PTC] Ditemukan " . count($all) . " iklan");
        if (!$pending) { logg('s', "[PTC] Semua iklan sudah ke-claim!"); break; }
        if ($pass > 1) logg('w', "[PTC] Pass #$pass: " . count($pending) . " iklan belum ke-claim");

        foreach ($pending as $ad) {
            logg('i', "[PTC] Ad #{$ad['id']} | {$ad['reward']}c | {$ad['duration']}s");
            $ok = false;
            for ($t = 1; $t <= MAX_PTC_RETRY; $t++) {
                if ($t > 1) logg('w', "[PTC] Ad #{$ad['id']} retry $t/" . MAX_PTC_RETRY);
                [$success, $current_balance] = claim_one_ad($ad, $current_balance ?? 0.0);
                if ($success === null) return -1;
                if ($success) {
                    $claimed[] = $ad['id']; $ok = true; break;
                }
                sleep(2);
            }
            if (!$ok) logg('e', "[PTC] Ad #{$ad['id']} gagal " . MAX_PTC_RETRY . "x");
        }
    }
    return 0;
}

function load_config(): array {
    if (!file_exists(CONFIG_FILE)) {
        clear_screen();
        banner_main();
        echo WHT . "  Config Setup — OurCoinCash" . RST . "\n";
        echo WHT . "  ─────────────────────────────" . RST . "\n";
        echo WHT . "  API Key (Waryono) : " . RST;
        $apikey = prompt('');
        echo WHT . "  Email             : " . RST;
        $email = prompt('');
        echo WHT . "  Password          : " . RST;
        $password = prompt('');
        $cfg = ['apikey' => $apikey, 'email' => $email, 'password' => $password];
        file_put_contents(CONFIG_FILE, json_encode($cfg, JSON_PRETTY_PRINT));
        logg('s', "Config tersimpan: " . CONFIG_FILE);
        sleep(1);
        return $cfg;
    }

    $cfg = json_decode(file_get_contents(CONFIG_FILE), true);
    if (!is_array($cfg)) $cfg = [];
    $cfg += ['apikey' => '', 'email' => '', 'password' => ''];

    if (empty($cfg['apikey']) && !empty($cfg['apikey_waryono'])) {
        $cfg['apikey'] = $cfg['apikey_waryono'];
        unset($cfg['apikey_waryono']);
        file_put_contents(CONFIG_FILE, json_encode($cfg, JSON_PRETTY_PRINT));
    }

    return $cfg;
}

function clear_screen(): void {
    if (is_tty()) system('clear');
}

function banner_main(): void {
    echo WHT . "═══════════════════════════════════════════════" . RST . "\n";
    echo YEL . "       BOT OURCOINCASH.XYZ" . RST . "\n";
    echo CYN . "       Credit by t.me/Hello_world092" . RST . "\n";
    echo WHT . "═══════════════════════════════════════════════" . RST . "\n";
}

function banner_account(string $email): void {
    echo WHT . "═══════════════════════════════════════════════" . RST . "\n";
    echo WHT . "Akun : " . CYN . mask_email($email) . RST . "\n";
    echo WHT . "───────────────────────────────────────────────" . RST . "\n";
}

function run_faucet_loop(): void {
    global $CFG;
    clear_screen(); banner_main();
    echo WHT . "Akun : " . CYN . mask_email($CFG['email']) . RST . "\n";
    echo WHT . "Mode : " . CYN . "Auto (PTC → Faucet)" . RST . "\n";
    echo WHT . "───────────────────────────────────────────────" . RST . "\n";
    while (true) {
        if (!ensure_login()) { sleep(3); continue; }
        $bal = b();
        if ($bal !== null) logg('i', "Balance: " . number_format($bal, 2) . " coins");

        $ptc = run_ptc();
        if ($ptc == -1) { logg('w', "[PTC] session expired, re-login..."); sleep(2); continue; }

        $r = run_faucet();
        if ($r == -1) { logg('w', "[FAUCET] session expired, re-login..."); sleep(2); continue; }
        sleep(1);
    }
}

function main(): void {
    global $CFG;
    tty_ok_or_die();
    $CFG = load_config();
    clear_screen(); banner_main();
    echo WHT . "Akun : " . CYN . mask_email($CFG['email'] ?? '') . RST . "\n";
    if (!ensure_login()) {
        logg('e', "Login gagal");
        return;
    }
    $bal = b();
    if ($bal !== null) logg('i', "Balance: " . number_format($bal, 2) . " coins");
    run_faucet_loop();
}

main();