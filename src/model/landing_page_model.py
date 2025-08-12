from pydantic import BaseModel


class HeroSection(BaseModel):
    subtitle: str
    title: str
    description: str


class LandingPageSection(BaseModel):
    title: str
    description: str
    imageURL: str


class LandingPageModel(BaseModel):
    hero: HeroSection
    section_1: LandingPageSection
    section_2: LandingPageSection
    section_3: LandingPageSection
