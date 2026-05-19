<?php
date_default_timezone_set('Asia/Tokyo');

function usage() {
    fwrite(STDERR, "Usage: php scripts/send_mail_php.php --to <email> --subject <subject> --body <body>\n");
    fwrite(STDERR, "       php scripts/send_mail_php.php --to <email> --subject <subject> --body-file <path>\n");
    exit(1);
}

function arg_value($name, $default = '') {
    global $argv;
    for ($i = 1; $i < count($argv); $i++) {
        if ($argv[$i] === $name && isset($argv[$i + 1])) {
            return $argv[$i + 1];
        }
    }
    return $default;
}

function has_arg($name) {
    global $argv;
    return in_array($name, $argv, true);
}

function clean_line($value) {
    return trim(str_replace(array("\r", "\n"), ' ', (string)$value));
}

function swork_send_mail($to, $subject, $body, $from, $reply_to) {
    $headers = implode("\r\n", array(
        'From: ' . $from,
        'Reply-To: ' . $reply_to,
        'MIME-Version: 1.0',
        'Content-Type: text/plain; charset=UTF-8',
        'Content-Transfer-Encoding: base64',
        'X-Mailer: SWork CLI',
    ));
    $encoded_subject = '=?UTF-8?B?' . base64_encode($subject) . '?=';
    $encoded_body = chunk_split(base64_encode($body));
    return mail($to, $encoded_subject, $encoded_body, $headers);
}

$to = clean_line(arg_value('--to'));
$subject = clean_line(arg_value('--subject'));
$from = clean_line(arg_value('--from', 'sales@exbridge.jp'));
$reply_to = clean_line(arg_value('--reply-to', $from));
$body = arg_value('--body');
$body_file = arg_value('--body-file');

if ($body_file !== '') {
    if (!is_file($body_file)) {
        fwrite(STDERR, "body file not found: " . $body_file . "\n");
        exit(1);
    }
    $body = file_get_contents($body_file);
}

if ($to === '' || $subject === '' || trim($body) === '') {
    usage();
}

if (has_arg('--dry-run')) {
    echo "dry-run\n";
    echo "from: " . $from . "\n";
    echo "to: " . $to . "\n";
    echo "subject: " . $subject . "\n";
    echo $body . "\n";
    exit(0);
}

$ok = swork_send_mail($to, $subject, $body, $from, $reply_to);
if (!$ok) {
    fwrite(STDERR, "mail() failed\n");
    exit(1);
}
echo "sent: " . $to . "\n";
