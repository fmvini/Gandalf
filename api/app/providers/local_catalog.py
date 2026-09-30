"""Small editorial catalog. No remote calls, credentials, audio or book copies."""

import re
import unicodedata
from urllib.parse import quote
from uuid import NAMESPACE_URL, UUID, uuid5

from app.schemas.book import BookItem, BookSearchResponse


def normalize(value: str) -> str:
    return " ".join(
        re.findall(
            r"[a-z0-9]+",
            unicodedata.normalize("NFKD", value.casefold())
            .encode("ascii", "ignore")
            .decode(),
        )
    )


# Descriptions and atmosphere classifications are editorial. New instrument
# and detective-fiction tags have sources in docs/catalog-metadata.md;
# they describe the work, not every recording/arrangement returned by a search.
BOOK_ROWS = [
    (
        "Duna",
        "Frank Herbert",
        "Dune",
        "ficção científica,épico,mistério,deserto,política",
        "Disputas políticas e ecológicas em um planeta desértico.",
    ),
    (
        "O Hobbit",
        "J. R. R. Tolkien",
        "The Hobbit",
        "fantasia,aventura,acolhedor,viagem",
        "Uma jornada por terras fantásticas em busca de um tesouro.",
    ),
    (
        "O Senhor dos Anéis",
        "J. R. R. Tolkien",
        "The Lord of the Rings",
        "fantasia,aventura,épico,viagem",
        "Uma missão que atravessa povos e paisagens da Terra Média.",
    ),
    (
        "O Feiticeiro de Terramar",
        "Ursula K. Le Guin",
        "A Wizard of Earthsea",
        "fantasia,aventura,introspectivo",
        "Um jovem mago aprende sobre poder, equilíbrio e responsabilidade.",
    ),
    (
        "A Mão Esquerda da Escuridão",
        "Ursula K. Le Guin",
        "The Left Hand of Darkness",
        "ficção científica,política,introspectivo",
        "Um emissário encontra uma sociedade que desafia suas certezas.",
    ),
    (
        "Fundação",
        "Isaac Asimov",
        "Foundation",
        "ficção científica,épico,política",
        "Um projeto tenta preservar o conhecimento diante da queda de um império.",
    ),
    (
        "Frankenstein",
        "Mary Shelley",
        "Frankenstein",
        "terror,introspectivo,triste,ficção científica",
        "A criação de uma vida coloca criador e criatura diante da solidão.",
    ),
    (
        "Drácula",
        "Bram Stoker",
        "Dracula",
        "terror,mistério,sombrio",
        "Cartas e diários revelam uma ameaça que se espalha pela Inglaterra.",
    ),
    (
        "O Cão dos Baskervilles",
        "Arthur Conan Doyle",
        "The Hound of the Baskervilles",
        "mistério,sombrio,aventura,detetive",
        "Sherlock Holmes investiga uma morte cercada por uma antiga lenda.",
    ),
    (
        "Orgulho e Preconceito",
        "Jane Austen",
        "Pride and Prejudice",
        "romance,acolhedor,política",
        "Encontros e julgamentos apressados em uma sociedade de convenções rígidas.",
    ),
    (
        "Jane Eyre",
        "Charlotte Brontë",
        "Jane Eyre",
        "romance,introspectivo,sombrio",
        "Uma jovem busca autonomia e afeto sem abrir mão de seus princípios.",
    ),
    (
        "Anne de Green Gables",
        "L. M. Montgomery",
        "Anne of Green Gables",
        "acolhedor,esperançoso,aventura",
        "Uma menina imaginativa transforma sua vida em uma pequena comunidade.",
    ),
    (
        "O Jardim Secreto",
        "Frances Hodgson Burnett",
        "The Secret Garden",
        "acolhedor,esperançoso,calmo",
        "A descoberta de um jardim aproxima crianças marcadas pela solidão.",
    ),
    (
        "O Pequeno Príncipe",
        "Antoine de Saint-Exupéry",
        "The Little Prince",
        "fantasia,introspectivo,acolhedor,triste",
        "Uma viagem entre planetas convida a pensar sobre vínculos e cuidado.",
    ),
    (
        "A Metamorfose",
        "Franz Kafka",
        "The Metamorphosis",
        "introspectivo,sombrio,triste",
        "Uma transformação inesperada expõe as tensões de uma família.",
    ),
    (
        "A Volta ao Mundo em Oitenta Dias",
        "Jules Verne",
        "Around the World in Eighty Days",
        "aventura,viagem,esperançoso",
        "Uma aposta leva um viajante a tentar dar a volta ao mundo.",
    ),
    (
        "Neuromancer",
        "William Gibson",
        "Neuromancer",
        "ficção científica,sombrio,mistério,cyberpunk",
        "Um hacker entra em uma operação entre redes, corporações e inteligências artificiais.",
    ),
    (
        "Solaris",
        "Stanisław Lem",
        "Solaris",
        "ficção científica,mistério,introspectivo",
        "Cientistas enfrentam os limites da compreensão diante de um oceano alienígena.",
    ),
]

BOOKS = [
    BookItem(
        id=uuid5(NAMESPACE_URL, "gandalf:book:" + original),
        title=title,
        authors=[author],
        description=description,
        genres=tags.split(","),
        subjects=tags.split(","),
        provider="local",
        external_id=original,
        external_url="https://openlibrary.org/search?q="
        + quote(original + " " + author),
    )
    for title, author, original, tags, description in BOOK_ROWS
]

# Durations vary by recording. Five minutes per item is a planning estimate,
# never presented as recording metadata. Links intentionally open a search.
MUSIC_ROWS = [
    ("Gymnopédie No. 1", "Erik Satie", "calmo,introspectivo,acolhedor,piano", "low", False),
    ("Clair de lune", "Claude Debussy", "calmo,atmosférico,acolhedor,piano", "low", False),
    ("Spiegel im Spiegel", "Arvo Pärt", "calmo,introspectivo,triste,piano", "low", False),
    (
        "On the Nature of Daylight",
        "Max Richter",
        "triste,cinematográfico,introspectivo",
        "low",
        False,
    ),
    ("Ambre", "Nils Frahm", "calmo,acolhedor,introspectivo,piano", "low", False),
    ("Saman", "Ólafur Arnalds", "calmo,atmosférico,introspectivo", "low", False),
    (
        "An Ending (Ascent)",
        "Brian Eno",
        "calmo,atmosférico,ficção científica",
        "low",
        False,
    ),
    ("Weightless", "Marconi Union", "calmo,atmosférico,mistério", "low", False),
    ("Avril 14th", "Aphex Twin", "calmo,introspectivo,acolhedor,piano", "low", False),
    ("River Flows in You", "Yiruma", "calmo,romance,esperançoso,piano", "low", False),
    (
        "Comptine d'un autre été, l'après-midi",
        "Yann Tiersen",
        "calmo,acolhedor,cinematográfico,piano",
        "low",
        False,
    ),
    (
        "Concerning Hobbits",
        "Howard Shore",
        "fantasia,aventura,acolhedor,cinematográfico",
        "medium",
        False,
    ),
    (
        "The Fellowship of the Ring: The Breaking of the Fellowship",
        "Howard Shore",
        "fantasia,épico,triste,cinematográfico",
        "medium",
        True,
    ),
    ("Time", "Hans Zimmer", "épico,cinematográfico,esperançoso", "medium", False),
    (
        "Cornfield Chase",
        "Hans Zimmer",
        "ficção científica,atmosférico,cinematográfico",
        "medium",
        False,
    ),
    (
        "Blade Runner Blues",
        "Vangelis",
        "cyberpunk,ficção científica,atmosférico,triste",
        "low",
        False,
    ),
    (
        "Mesa",
        "Hans Zimmer & Benjamin Wallfisch",
        "cyberpunk,sombrio,mistério,deserto",
        "medium",
        False,
    ),
    (
        "The Imperial March",
        "John Williams",
        "épico,aventura,cinematográfico,sombrio",
        "high",
        False,
    ),
    (
        "Ride of the Valkyries",
        "Richard Wagner",
        "épico,aventura,fantasia",
        "high",
        False,
    ),
    ("No Surprises", "Radiohead", "triste,calmo,introspectivo", "low", True),
    ("Space Song", "Beach House", "atmosférico,triste,introspectivo", "low", True),
    ("Holocene", "Bon Iver", "calmo,introspectivo,viagem", "low", True),
    ("Here Comes the Sun", "The Beatles", "esperançoso,acolhedor", "medium", True),
    ("Don't Stop Me Now", "Queen", "alegre,aventura", "high", True),
    (
        "Walking on Sunshine",
        "Katrina and the Waves",
        "alegre,esperançoso",
        "high",
        True,
    ),
]

MUSIC = [
    {
        "id": str(uuid5(NAMESPACE_URL, "gandalf:music:" + title + artist)),
        "title": title,
        "artist": artist,
        "tags": tags.split(","),
        "energy": energy,
        "has_vocals": vocals,
        "estimated_duration_ms": 300_000,
        "links": {
            "search": "https://www.youtube.com/results?search_query="
            + quote(title + " " + artist)
        },
    }
    for title, artist, tags, energy, vocals in MUSIC_ROWS
]


class LocalBookProvider:
    name = "local"

    async def search(self, title: str, limit: int) -> BookSearchResponse:
        terms = normalize(title).split()
        matches = [
            book.model_copy(deep=True)
            for book in BOOKS
            if all(
                term
                in normalize(
                    book.title + " " + " ".join(book.authors) + " " + book.external_id
                )
                for term in terms
            )
        ]
        return BookSearchResponse(items=matches[:limit], total=len(matches))

    @staticmethod
    def get_by_id(book_id: UUID) -> BookItem | None:
        return next(
            (book.model_copy(deep=True) for book in BOOKS if book.id == book_id), None
        )
