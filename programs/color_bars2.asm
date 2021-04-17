        .word $0801
        * = $0801

        LDA #$00
        STA $FB
        STA $FD
        LDA #$04
        STA $FC
        LDA #$D8
        STA $FE

        LDX #$00
loop2   LDY #$27
loop1   TXA
        STA ($FD),Y
        LDA #$A0
        STA ($FB),Y
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

        JSR $E544

        LDA #$00
        STA $FB
        STA $FD
        LDA #$04
        STA $FC
        LDA #$D8
        STA $FE

        LDY #$1F
loop3
        LDA ($FB),Y
        ADC #$01
        STA ($FB),Y
        BNE loop3
        DEY
        BNE loop3
        JSR $E544

        BRK
