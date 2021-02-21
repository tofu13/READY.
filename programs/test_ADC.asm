        * = $C000
            lda #$10
.loop
           SEC
            sbc #$01
            jmp .loop

