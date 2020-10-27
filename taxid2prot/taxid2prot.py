"""Fasta protein sequence download module using selenium ChromeDriver."""
import os
import re
from typing import List, Union
import requests
from fake_useragent import UserAgent
from tqdm import tqdm
try:
    from . import multiproc_utils
except ImportError:
    import multiproc_utils


class Parser:
    """
    A class for downloading protein sequence files in * .fasta format
    using selenium ChromeDriver.

    Parameters 🧾
    ----------
    path_to_save: str
        Path to the directory where the files will be saved.
    executable_path: str
        Path to the executable file chromedriver.

    Examples 👀
    ----------
    >>> folder_to_download = "."
    >>> taxonimy_to_parse = [269799, 436]
    >>> parser = ParseProtein(folder_to_download)
    >>> parser.parse(taxonimy_to_parse)
    And now look at `folder_to_download`/proteins/ for your files.
    """

    def __init__(self, path_to_save: str):
        if os.path.isdir(path_to_save):
            self.download_folder: str = self.__create_download_folder(path_to_save)
            print(f"Your files will be save in {self.download_folder}.")
        else:
            raise ValueError(f"Неверный путь для сохранения: {path_to_save}")
        self.url = "https://www.uniprot.org/uniprot/?query=organism:{}&format=fasta"
        self.session = None

    @staticmethod
    def __create_download_folder(path: str) -> str:
        """Create a folder to save files."""

        attempts = 40
        for i in range(attempts):
            new_path = os.path.join(path, f"proteins({i})")
            if not os.path.exists(new_path):
                os.makedirs(new_path)
                return new_path
        raise ValueError("ERROR: Unable to create folder.")

    def init_session(self) -> None:
        """Init Chrome driver session."""

        # Init options:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": UserAgent().random})

    @staticmethod
    def find_organism_name(text: str) -> str:
        """Find scientific organism name in fasta."""

        organism_name = "no_name"
        os_pattern = r"OS=([A-Za-z]+\s[A-Za-z]+)"
        result = re.search(os_pattern, text)
        if result:
            organism_name = result.group(1).lower().replace(" ", "_")
        return organism_name

    # pylint: disable=bad-continuation
    def save_file_as_fasta(
        self, organism_name: str, tax_id: int, text_to_write: str
    ) -> None:
        """Save file in fasta format."""

        file_name = os.path.join(
            self.download_folder, f"{organism_name}_{tax_id}.fasta"
        )
        if not os.path.exists(file_name):
            with open(file_name, "w") as fasta_file:
                fasta_file.write(text_to_write)
        else:
            print(f"ERROR: File {file_name} is already exists.")

    def download_proteins(self, tax_id: int) -> None:
        """Algorithm for downloading a sequence of proteins by taxonomy id."""

        response = self.session.get(self.url.format(tax_id))
        if response.status_code != 200:
            print(f"ERROR: Problems with API. Status code = {response.status_code}.")
            return

        fasta_text: str = response.text
        if not fasta_text:
            print(f"WARNING: No proteins from taxonomy = {tax_id}.")
            return

        organism_name: str = self.find_organism_name(fasta_text)
        self.save_file_as_fasta(organism_name, tax_id, fasta_text)

    def parse(self, tax_ids: Union[List[int], int]) -> None:
        """
        Start parsing process.
        To avoid problems, the data will be loaded in batches of 10 pieces.

        Parameters 🧾
        ----------
        tax_ids: Union[List[int], int]
            NCBI tax ID Associated which is associated to the refering INSDC accession number.
        """

        # Convert idx to List[idx]:
        if isinstance(tax_ids, int):
            tax_ids = [tax_ids]

        # Start parsing:
        self.init_session()
        for tax_id in tqdm(tax_ids):
            self.download_proteins(tax_id)
        print(f"The downloaded files are located here: {self.download_folder}.")


if __name__ == "__main__":
    
    # Testing:
    from multiprocessing import Pool

    # pylint: disable=invalid-name
    cpu_count = multiproc_utils.get_cpu_count() + 5
    tax_indices = [435, 436, 437, 438, 439, 440, 441, 442, 443]
    tax_indices = multiproc_utils.get_batches(tax_indices, cpu_count)

    folder_to_download = "."
    parser = Parser(folder_to_download)

    pool = Pool(cpu_count)
    pool.map(parser.parse, tax_indices)
