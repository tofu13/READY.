        * = $C000
        CLC
        LDA #$00
.loop   ADC #$01
        BNE .loop
        BRK

