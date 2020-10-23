"""Fasta protein sequence download module using selenium ChromeDriver."""
import os
import re
from time import sleep
from typing import List, Union
from fake_useragent import UserAgent
from selenium import webdriver
from tqdm import tqdm
import multiproc_utils

# pylint: disable=line-too-long


class ParseProtein:
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
    >>> parser = ParseProtein(folder_to_download)
    >>> parser.parse([435, 436])
    And now look at folder_to_download/proteins/ for your files.
    """

    def __init__(self, path_to_save: str, executable_path: str = "chromedriver"):
        self.executable_path = executable_path
        if self.__check_path(path_to_save):
            self.download_folder: str = self.__create_download_folder(path_to_save)
            print(f"Your files will be save in {self.download_folder}.")
        else:
            raise ValueError(f"Неверный путь для сохранения: {path_to_save}")
        self.driver = None

    @staticmethod
    def __create_download_folder(path: str) -> str:
        """Create a folder to save files."""

        attempts = 40
        for i in range(attempts):
            new_path = os.path.join(path, f"proteins({i})")
            if not os.path.exists(new_path):
                os.makedirs(new_path)
                return new_path
        raise ValueError("Unable to create folder.")

    @staticmethod
    def __check_path(path: str) -> bool:
        """Check is the path a folder."""

        return os.path.isdir(path)

    def init_session(self) -> None:
        """Init Chrome driver session."""

        # Init options:
        options = webdriver.ChromeOptions()

        # Add fake user agent:
        fake_user_agent = UserAgent(verify_ssl=False).random
        options.add_argument("user-agent=" + fake_user_agent)

        # Add download directory:
        prefs = {"download.default_directory": self.download_folder}
        options.add_experimental_option("prefs", prefs)

        # Create driver:
        self.driver = webdriver.Chrome(self.executable_path, options=options)
        self.driver.implicitly_wait(3)

    def download_proteins(self, tax_id: int) -> None:
        """Algorithm for Chrome for downloading a sequence of proteins.
        """

        url = f"https://www.ncbi.nlm.nih.gov/protein?term=txid{tax_id}[Organism]"
        self.driver.get(url)

        # Click on button "Send to":
        send_to_button = "content_header.send_to.align_right.jig-ncbipopper"
        self.driver.find_element_by_class_name(send_to_button).click()

        # Choose "File" in radio buttons:
        file_button = "EntrezSystem2.PEntrez.Protein.Sequence_ResultsPanel.Sequence_DisplayBar.SendTo"
        self.driver.find_element_by_name(file_button).click()

        # Change fromat to FASTA:
        formats = "EntrezSystem2.PEntrez.Protein.Sequence_ResultsPanel.Sequence_DisplayBar.FFormat"
        self.driver.find_element_by_name(formats).send_keys("F")

        # Download:
        create_file = "EntrezSystem2.PEntrez.Protein.Sequence_ResultsPanel.Sequence_DisplayBar.SendToSubmit"
        self.driver.find_element_by_name(create_file).click()

        # Wait for downloading the file:
        sleep(3)

    def are_files_downloaded(self) -> bool:
        """Go to the file upload page and return if the files are uploaded.
        """

        if not self.driver.current_url.startswith("chrome://downloads"):
            self.driver.get("chrome://downloads/")

        js_script = """
                var items = document.querySelector('downloads-manager')
                    .shadowRoot.getElementById('downloadsList').items;
                if (items.every(e => e.state === "COMPLETE"))
                    return items.map(e => e.fileUrl || e.file_url);
            """
        return not bool(self.driver.execute_script(js_script))

    def wait_until_files_download(self, close_driver: bool = False) -> None:
        """Sleep while files are downloading."""

        print("Wait for all files to download.")
        num = 0
        while True:
            sleep(2)
            num += 1
            if self.are_files_downloaded():
                if num % 60 == 0:
                    print("Still wait for the download, it may take a long time...")
            else:
                print("The batch of files has been downloaded, continue parsing.")
                break

        if close_driver:
            self.driver.close()

    def rename_files(self) -> None:
        """Rename the files by the name of the organisms they belong to."""

        # Get all *.fasta files in folder:
        files = os.listdir(self.download_folder)
        files = [x for x in files if x.endswith(".fasta") and x.startswith("sequence")]

        pattern_to_find_name = r"\[([A-Za-z0-9_\s]+)\]"
        for file in files:
            # Read first line with the name of the organism:
            old_name = os.path.join(self.download_folder, file)
            with open(old_name) as fasta_file:
                first_line = fasta_file.readline()

            # Find the name of the organism:
            new_name = re.findall(pattern_to_find_name, first_line)

            # Rename file:
            if new_name:
                new_name = os.path.join(self.download_folder, new_name[0])
            else:
                print(f"Что-то не так с {old_name}, не могу переименовать.")
                continue
            os.rename(old_name, f"{new_name}.fasta")

    def parse(self, tax_ids: Union[List[int], int], batch_size: int = 10) -> None:
        """
        Start parsing process.
        To avoid problems, the data will be loaded in batches of 10 pieces.

        Parameters 🧾
        ----------
        tax_ids: Union[List[int], int]
            NCBI tax ID Associated which is associated to the refering INSDC accession number.
        batch_size: int
            The number of allowed files to download at the same time.
        """

        print("To avoid problems, the data will be loaded in batches of 10 pieces.")

        # Convert idx to List[idx]:
        if isinstance(tax_ids, int):
            tax_ids = [tax_ids]

        # Start parsing:
        self.init_session()
        for i, tax_id in enumerate(tqdm(tax_ids)):
            self.download_proteins(tax_id)

            if i % batch_size == 0 and i != 0:
                self.wait_until_files_download()

        self.wait_until_files_download(close_driver=True)
        self.rename_files()
        print(f"The downloaded files are located here: {self.download_folder}.")


if __name__ == "__main__":
    from multiprocessing import Pool

    cpu_count = multiproc_utils.get_cpu_count()
    tax_indices = [435, 436, 437, 438, 439, 440, 441, 442, 443]
    tax_indices = multiproc_utils.get_batches(tax_indices, cpu_count)

    folder_to_download = "."
    parser = ParseProtein(folder_to_download)

    pool = Pool(cpu_count)
    pool.map(parser.parse, tax_indices)
