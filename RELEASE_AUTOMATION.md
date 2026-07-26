# Android-Release mit einem Befehl

Das Release-Skript baut die Android-App immer aus einem ausdrücklich
gewählten Git-Commit. Es:

1. löst den Commit auf und erstellt dafür einen temporären, sauberen Worktree,
2. kopiert genau dessen Webdateien in das Capacitor-Projekt,
3. erhöht den Versionscode (oder verwendet einen angegebenen höheren Code),
4. führt `npm run sync:android` und `bundleRelease` aus,
5. signiert die AAB mit dem vorhandenen Play-Store-Schlüssel,
6. entpackt die AAB und vergleicht alle eingebetteten Webdateien per SHA-256,
7. schreibt einen JSON- und Markdown-Prüfbericht.

Beispiel:

```powershell
.\scripts\build-android-release.ps1 `
  -AndroidProject "C:\Pfad\zum\Capacitor-Projekt" `
  -Commit "origin/main" `
  -VersionName "1.8.5" `
  -Keystore "C:\Pfad\world-revolution.jks" `
  -KeyAlias "WRN_KEY"
```

Ohne `-VersionCode` verwendet das Skript automatisch den vorhandenen Code plus
eins. Ein bereits verwendeter oder kleinerer Code wird abgelehnt. Ohne
`-VersionName` übernimmt es automatisch die Version aus `WRN_CONFIG` des
gewählten Commits. Eine abweichende Android- und Webversion wird abgelehnt.

Das Kennwort wird nicht im Repository oder Bericht gespeichert. `jarsigner`
fragt es sicher im Terminal ab. Für lokale Automatisierung können die
temporären Umgebungsvariablen `WRN_KEYSTORE_PASSWORD` und
`WRN_KEY_PASSWORD` gesetzt werden; das Skript nutzt dann die
`jarsigner`-Option `:env`, sodass Kennwörter nicht in der Befehlszeile stehen.
