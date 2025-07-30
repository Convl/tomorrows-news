    @property
    def additional_infos_list(self) -> list[AdditionalInfo] | None:
        """Convert JSON back to list[AdditionalInfo]."""
        return [AdditionalInfo(**item) for item in self.additional_infos] if self.additional_infos else None

    @additional_infos_list.setter
    def additional_infos_list(self, value: list[AdditionalInfo] | None):
        """Convert list[AdditionalInfo] to JSON for storage."""
        self.additional_infos = [item.model_dump() for item in value] if value else None

    class AdditionalInfo(BaseModel):
    """Supplementary information about an event with an importance weight. This can be used to provide additional context or details about the event."""

    info_name: str = Field(
        description="The name of the additional piece of information (e.g. 'registration_link', 'reference_number', 'accreditation_deadline', etc.)"
    )
    info_value: str = Field(
        description="The value of the additional piece of information (e.g. 'https://www.example.com/registration', '1234567890', '2025-08-01', etc.)"
    )
    weight: float = Field(
        description="A numerical weight (0.0 to 1.0) indicating how helpful this piece of additional information will be in disambiguating the event that it belongs to from other, similar events pertaining to the same topic. 0.0 means not helpful at all, 1.0 means extremely helpful."
    )