from dataclasses import dataclass, field


@dataclass(slots=True)
class Bus:
    nmi_producers: set = field(default_factory=set)
    nmi_raised: bool = False  # Flag for ramp up to be read by consumers (CPU)
    irq_producers: set = field(default_factory=set)

    def nmi_set(self, source):
        self.nmi_raised |= not bool(self.nmi_producers)
        self.nmi_producers.add(source)

    def nmi_clear(self, source):
        self.nmi_producers.discard(source)
        # Keep flag true if any sources and still unconsumed
        self.nmi_raised &= bool(self.nmi_producers)

    @property
    def nmi(self) -> bool:
        """True if a ramp up occured and still not read"""
        raised = self.nmi_raised
        self.nmi_raised = False
        return raised

    def irq_set(self, source):
        self.irq_producers.add(source)

    def irq_clear(self, source):
        self.irq_producers.discard(source)

    @property
    def irq(self) -> bool:
        """True if any producer is set"""
        return bool(self.irq_producers)
