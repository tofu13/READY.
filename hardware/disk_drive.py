import d64


class Drive:
    image_file: str

    def set_imagefile(self, image_file: str):
        self.image_file = image_file

    def set_filename(self, filename: str):
        self.filename = filename

    def read(self, filename: bytes):
        if filename == b"$":
            with d64.DiskImage(self.image_file) as image:
                return list(image.directory())
        else:
            with d64.DiskImage(self.image_file) as image:
                with image.path(filename).open() as in_file:
                    return in_file.read()

    def readbyte(self):
        with d64.DiskImage(self.image_file) as image:
            with image.path(self.filename).open() as in_file:
                self.data = in_file.read()
        for byte in data:
            yield byte
