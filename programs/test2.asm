    * = $C000
        LDA .data
        LDX .data+1
        LDY .data
        BRK
.data   !byte $FF,$FE,$FD

