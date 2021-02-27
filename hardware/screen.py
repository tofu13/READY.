class Screen:
    memory = None

    def init(self):
        pass
    #   self.memory.write_watchers.append([0x0100, 0x07FF, self.refresh])

    def refresh(self, address, value):
        print("\n".join(
            ["".join(map(chr,self.memory[1024 + i*40: 1024 + i*40 + 39])) for i in range(0, 24, 40)])
        )
        return value
