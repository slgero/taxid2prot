import os
import re
from time import sleep
from typing import List, Union
from fake_useragent import UserAgent
from selenium import webdriver
from tqdm.notebook import tqdm


class ParseProtein:
    """
    Examples
    --------
    >>> folder_to_download = "C:\\Users\\SS\\Documents"
    >>> parser = ParseProtein(folder_to_download)
    >>> parser.parse([435, 436])
    And now look at folder_to_download/proteins/
    """
    def __init__(self, path_to_save: str):
        if self.__check_path(path_to_save):
            self.download_folder = self.__create_download_folder(path_to_save)
            print(f"Your files will be save in {self.download_folder}.")
        else:
            raise ValueError(f'Неверный путь для сохранения: {path_to_save}')
        self.driver = None
        
    @staticmethod
    def __create_download_folder(path: str) -> str:
        for i in range(20):
            new_path = os.path.join(path, f'proteins({i})')
            if not os.path.exists(new_path):
                os.makedirs(new_path)
                return new_path
    
    @staticmethod
    def __check_path(path: str) -> bool:
        return os.path.isdir(path)
    
    def init_session(self) -> None:
        # Init options:
        options = webdriver.ChromeOptions()
        
        # Add fake user agent:
        fake_user_agent = UserAgent(verify_ssl=False).random
        options.add_argument("user-agent=" + fake_user_agent)
        
        # Add download directory:
        prefs = {"download.default_directory" : self.download_folder}
        options.add_experimental_option("prefs", prefs)
        
        # Create driver:
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(3)

    def download_proteins(self, tax_id: int):
        url = f"https://www.ncbi.nlm.nih.gov/protein?term=txid{tax_id}[Organism]"
        self.driver.get(url)
        
        # Click on button "Send to":
        send_to_button = 'content_header.send_to.align_right.jig-ncbipopper'
        self.driver.find_element_by_class_name(send_to_button).click()
        
        # Choose "File" in radio buttons:
        file_button = 'EntrezSystem2.PEntrez.Protein.Sequence_ResultsPanel.Sequence_DisplayBar.SendTo'
        self.driver.find_element_by_name(file_button).click()
        
        # Change fromat to FASTA:
        formats = 'EntrezSystem2.PEntrez.Protein.Sequence_ResultsPanel.Sequence_DisplayBar.FFormat'
        self.driver.find_element_by_name(formats).send_keys('F')
        
        sleep(1)
        # Download:
        create_file = "EntrezSystem2.PEntrez.Protein.Sequence_ResultsPanel.Sequence_DisplayBar.SendToSubmit"
        self.driver.find_element_by_name(create_file).click()
        sleep(3)
        
        
    def every_downloads_chrome(self):
        if not self.driver.current_url.startswith("chrome://downloads"):
            self.driver.get("chrome://downloads/")
        return self.driver.execute_script("""
            var items = document.querySelector('downloads-manager')
                .shadowRoot.getElementById('downloadsList').items;
            if (items.every(e => e.state === "COMPLETE"))
                return items.map(e => e.fileUrl || e.file_url);
            """)    
    
    def wait_until_files_download(self, close_driver: bool = False) -> None:
        print('Ждём загрузки всех файлов.')
        num = 0
        while True:
            pathes = self.every_downloads_chrome()
            sleep(10)
            num += 1
            if pathes is None:
                if num % 60 == 0:
                    print("Всё ещё ждём, это может занять долгое время.")
                continue
            else:
                print("Батч файлов загруженен, скачиваем дальше.")
                break
        
        if close_driver:
            self.driver.close()

    def rename_files(self):
        files = os.listdir(self.download_folder)
        files = [x for x in files if x.endswith(".fasta")]

        pattern_to_find_name = r"\[([A-Za-z0-9_\s]+)\]"
        for file in files:
            old_name = os.path.join(self.download_folder, file)
            with open(old_name) as file:
                first_line = file.readline()

            new_name = re.findall(pattern_to_find_name, first_line)
            if new_name:
                new_name = os.path.join(self.download_folder, new_name[0])
            else:
                print(f"Что-то не так с {old_name}, не могу переименовать.")
                continue
            os.rename(old_name, f'{new_name}.fasta')
            
    def parse(self, tax_ids: Union[List[int], int], batch_size: int = 10):
        print("Чтобы не возникало проблем, данные будут грузиться батчами по 10 штук.")
        
        if isinstance(tax_ids, int):
            tax_ids = [tax_ids]

        self.init_session()
        for i, tax_id in enumerate(tax_ids):
            self.download_proteins(tax_id)
            
            if i % 10 == 0 and i != 0:
                self.wait_until_files_download()
                
        self.wait_until_files_download(close_driver=True)
        self.rename_files()
                    