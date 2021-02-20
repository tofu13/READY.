        * = $C000
        SEC
        CLV
        LDA #$40
.loop   ADC #$40
        BRK

