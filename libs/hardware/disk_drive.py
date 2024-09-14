import d64


class Drive:
    image_file: str

    def set_imagefile(self, image_file: str):
        self.image_file = image_file

    def read(self, filename: bytes):
        if filename == b"$":
            buffer = bytearray(0)
            buffer.append(0)  # lo address - ignored
            buffer.append(0)  # hi address - ignored
            pointer = 0x0801
            with d64.DiskImage(self.image_file) as image:
                pointer += 0x1F
                buffer.append(pointer % 256)
                buffer.append(pointer // 256)
                buffer.append(0x00)  # 0 fixed
                buffer.append(0x00)  # 0 fixed
                buffer.append(0x12)  # Reverse
                buffer.append(0x22)  # "
                buffer.extend([0x20] * (16 - len(image.name)))  # Pad
                buffer.extend(image.name)  # Disk name
                buffer.append(0x22)  # "
                buffer.append(0x20)
                buffer.extend(image.id)
                buffer.append(0x20)
                buffer.append(image.dos_version)
                buffer.append(image.dos_type)
                buffer.append(0x00)

                for entry in image.glob(b"*"):
                    pointer += 28
                    buffer.append(pointer % 256)
                    buffer.append(pointer // 256)
                    buffer.append(entry.size_blocks % 256)
                    buffer.append(entry.size_blocks // 256)
                    buffer.extend([0x20] * 3)
                    buffer.append(0x22)  # "
                    buffer.extend(entry.name)
                    buffer.append(0x22)  # "
                    buffer.extend([0x20] * (18 - len(entry.name)))  # Pad
                    buffer.append(0x00)  # End of line

                pointer += 0x1E
                buffer.append(pointer % 256)
                buffer.append(pointer // 256)
                buffer.append(image.bam.total_free() % 256)
                buffer.append(image.bam.total_free() // 256)
                buffer.extend(b"BLOCKS FREE.")
                buffer.extend([0x20] * 13)  # Pad (?)
                buffer.extend([0x00] * 3)  # End of basic program

            return buffer
        else:
            with (
                d64.DiskImage(self.image_file) as image,
                image.path(filename).open() as in_file,
            ):
                return in_file.read()
