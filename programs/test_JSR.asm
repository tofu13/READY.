        *=0x801
        JSR .label1
        JSR .label2
        BRK

.label1 RTS
.label2 INX
        INY
        RTS