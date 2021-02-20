    * = $C000
        LDX #$00
        LDY #$02
        LDA .data,X
        INX
        LDA .data,Y
        INX
        LDA .data,X
        DEY
        LDA .data,Y
        BRK
.data   !byte $FF,$FE,$FD
