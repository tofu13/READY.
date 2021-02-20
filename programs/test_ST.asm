    * = $C000
    LDA #$01
    STA $0000
    LDX #$02
    TAY
    STX $0001
    STY $0002
    INX
    INX
    STA $01,X
    STA $01,Y
    STA ($01,X)
    STA ($02),Y
    BRK
