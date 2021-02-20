    * = $C000
        LDA .data
        LDX .data+1
        LDY .data+2
        BRK
.data   !byte $FF,$FE,$FD

