from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

# System directories that must never be targeted by destructive commands.
_SYSTEM_DIRS = r"(/bin|/sbin|/lib|/lib64|/usr|/etc|/boot|/sys|/proc|/dev|/run|/snap)"


class RiskLevel(Enum):
    SAFE = "safe"
    CAUTION = "caution"
    DANGEROUS = "dangerous"


@dataclass
class SafetyResult:
    level: RiskLevel
    warnings: list[str]


_DANGEROUS_PATTERNS: list[tuple[str, str]] = [
    # System file/directory destruction
    (rf"\\brm\\s+(-[a-zA-Z]*r[a-zA-Z]*\\s+|--recursive\\s+).*{_SYSTEM_DIRS}", "recursive delete on system path"),
    (rf"\\brm\\s+-[a-zA-Z]*rf\\s+.*{_SYSTEM_DIRS}", "force recursive delete on system path"),
    (rf"\\brm\\s+(-[a-zA-Z]*f)?\\s*{_SYSTEM_DIRS}/", "delete inside system directory"),
    # Disk / filesystem
    (r"\bmkfs\b", "filesystem format — will destroy all data"),
    (r"\bdd\s+.*\bof=/dev/", "raw disk write"),
    (r">\s*/dev/sd[a-z]", "direct write to block device"),
    (r"\bshred\b.*\b/dev/", "shred on block device"),
    # Sensitive paths — recursive delete
    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+|--recursive\s+).*(/|~|\$HOME|\.\.)", "recursive delete on sensitive path"),
    (r"\brm\s+-[a-zA-Z]*rf", "force recursive delete"),
    # Fork bomb
    (r":\(\)\s*\{\s*:\|:\s*&\s*\}\s*;", "fork bomb"),
    # World-writable system dirs
    (r"\bchmod\s+(-R\s+)?777\s+" + _SYSTEM_DIRS, "world-writable permissions on system path"),
    (r"\bchown\s+-R\s+.*\s+/\s*$", "recursive chown on root"),
    # Credential files
    (r">\s*/etc/(passwd|shadow|sudoers)", "overwriting credential file"),
    (r"\brm\b.*\b/etc/(passwd|shadow|sudoers)\b", "deleting credential file"),
    (r"\brm\b.*\b~/.ssh/", "deleting SSH keys"),
    # Boot / kernel
    (r"\brm\b.*\b/boot/(vmlinuz|initrd|grub)\b", "deleting boot files — system will be unbootable"),
]

_CAUTION_PATTERNS: list[tuple[str, str]] = [
    (r"\bsudo\b", "elevated privileges"),
    (r"\brm\b", "file deletion"),
    (r"\bchmod\b", "permission change"),
    (r"\bchown\b", "ownership change"),
    (r"\|.*\b(bash|sh|zsh)\b", "piping into shell"),
    (r"\bcurl\b.*\|.*\b(bash|sh|sudo)\b", "remote script execution"),
    (r"\bwget\b.*\|.*\b(bash|sh|sudo)\b", "remote script execution"),
    (r"\b>\s*/etc/", "writing to /etc"),
    (r"\bmv\b.*\s+/\s*$", "moving to root"),
    (r"\bkill\s+-9", "force kill"),
    (r"\bpkill\b", "process kill by pattern"),
    (r"\bsystemctl\s+(stop|disable|mask)", "stopping system service"),
    (r"\biptables\b", "firewall modification"),
]


def analyze(command: str) -> SafetyResult:
    warnings: list[str] = []
    level = RiskLevel.SAFE

    for pattern, description in _DANGEROUS_PATTERNS:
        if re.search(pattern, command):
            warnings.append(description)
            level = RiskLevel.DANGEROUS

    if level != RiskLevel.DANGEROUS:
        for pattern, description in _CAUTION_PATTERNS:
            if re.search(pattern, command):
                warnings.append(description)
                if level == RiskLevel.SAFE:
                    level = RiskLevel.CAUTION

    return SafetyResult(level=level, warnings=warnings)
