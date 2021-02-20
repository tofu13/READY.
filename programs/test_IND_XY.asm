    * = $C000
    LDX #$10
    LDY #$20
    LDA ($A0,X)
    LDA ($A0),Y
    BRK
.data !byte $03,$C0
