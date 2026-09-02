## Try to disprove a fix before closing the ticket

When the reported example already passes, do not repeat that example and
stop. Use this verification route:

1. Read the implementation that changed.
2. Name one realistic input that challenges an assumption in that
   implementation.
3. Run that targeted input.

Report `FIXED` only if the reported example and the targeted check both pass.
Otherwise report `NOT FIXED` and show the failing evidence.
