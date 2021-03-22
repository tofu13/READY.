        LDA #$00
        STA $FB
        STA $FD
        LDA #$04
        STA $FC
        LDA #$D8
        STA $FE

        LDX #$00
loop2   LDY #$27
loop1   LDA #$A0
        STA ($FB),Y
        TXA
        STA ($FD),Y
        DEY
        BPL loop1
        CLC
        LDA #$28
        ADC $FB
        STA $FB
        STA $FD
        BCC nocarry
        INC $FC
        INC $FE
nocarry
        INX
        CPX #$19
        BNE loop2
        BRK
