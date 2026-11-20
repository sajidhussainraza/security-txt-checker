# Record assets/demo.gif with VHS (https://github.com/charmbracelet/vhs)
# Terminal: 100 columns x 28 rows, dark theme, total run under 15 seconds.
# Install VHS, then run:  vhs assets/demo.tape
# Optimize the result under 5 MB with:
#   gifsicle -O3 --colors 128 assets/demo.gif -o assets/demo.gif
# Alternative: asciinema rec demo.cast, then convert with agg.

Output assets/demo.gif
Set Shell "bash"
Set FontSize 18
Set Width 1200
Set Height 560
Set Theme "Catppuccin Mocha"
Set Margin 16
Set MarginFill "#0B1220"

Hide
Type "cd security-txt-checker"
Enter
Sleep 500ms
Show

Type "python3 security_txt_checker.py https://github.com"
Enter
Sleep 2500ms

Type "python3 security_txt_checker.py https://example.com"
Enter
Sleep 3000ms

Type "python3 security_txt_checker.py https://google.com --json | head -12"
Enter
Sleep 2500ms
