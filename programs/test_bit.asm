    *=$2000
    LDX #$f0
    STX $02
    LDA #$81
    BIT $02
    EOR $02
    ORA $02
    AND $02
