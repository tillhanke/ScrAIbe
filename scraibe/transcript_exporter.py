import json
import time

from typing import Union
 
ALPHABET = [*"abcdefghijklmnopqrstuvwxyz"]

WHISPER_HALLUCINATIONS={
  "en": [
    " www.mooji.org",
  ],
  "nl": [
    " Ondertitels ingediend door de Amara.org gemeenschap",
    " Ondertiteld door de Amara.org gemeenschap",
    " Ondertiteling door de Amara.org gemeenschap"
  ],
  "de": [
    " Untertitelung aufgrund der Amara.org-Community"
    " Untertitel im Auftrag des ZDF für funk, 2017",
    " Untertitel von Stephanie Geiges",
    " Untertitel der Amara.org-Community",
    " Untertitel im Auftrag des ZDF, 2017",
    " Untertitel im Auftrag des ZDF, 2020",
    " Untertitel im Auftrag des ZDF, 2018",
    " Untertitel im Auftrag des ZDF, 2021",
    " Untertitelung im Auftrag des ZDF, 2021",
    " Copyright WDR 2021",
    " Copyright WDR 2020",
    " Copyright WDR 2019",
    " SWR 2021",
    " SWR 2020",
  ],
  "fr": [
    " Sous-titres réalisés para la communauté d'Amara.org",
    " Sous-titres réalisés par la communauté d'Amara.org",
    " Sous-titres fait par Sous-titres par Amara.org",
    " Sous-titres réalisés par les SousTitres d'Amara.org",
    " Sous-titres par Amara.org",
    " Sous-titres par la communauté d'Amara.org",
    " Sous-titres réalisés pour la communauté d'Amara.org",
    " Sous-titres réalisés par la communauté de l'Amara.org",
    " Sous-Titres faits par la communauté d'Amara.org",
    " Sous-titres par l'Amara.org",
    " Sous-titres fait par la communauté d'Amara.org"
    " Sous-titrage ST' 501",
    " Sous-titrage ST'501",
    " Cliquez-vous sur les sous-titres et abonnez-vous à la chaîne d'Amara.org",
    " ❤️ par SousTitreur.com",
  ],
  "it": [
    " Sottotitoli creati dalla comunità Amara.org",
    " Sottotitoli di Sottotitoli di Amara.org",
    " Sottotitoli e revisione al canale di Amara.org",
    " Sottotitoli e revisione a cura di Amara.org",
    " Sottotitoli e revisione a cura di QTSS",
    " Sottotitoli e revisione a cura di QTSS.",
    " Sottotitoli a cura di QTSS",
  ],
  "es": [
    " Subtítulos realizados por la comunidad de Amara.org",
    " Subtitulado por la comunidad de Amara.org",
    " Subtítulos por la comunidad de Amara.org",
    " Subtítulos creados por la comunidad de Amara.org",
    " Subtítulos en español de Amara.org",
    " Subtítulos hechos por la comunidad de Amara.org",
    " Subtitulos por la comunidad de Amara.org"
    " Más información www.alimmenta.com",
    " www.mooji.org",
  ],
  "gl": [
    " Subtítulos realizados por la comunidad de Amara.org"
  ],
  "pt": [
    " Legendas pela comunidade Amara.org",
    " Legendas pela comunidade de Amara.org",
    " Legendas pela comunidade do Amara.org",
    " Legendas pela comunidade das Amara.org",
    " Transcrição e Legendas pela comunidade de Amara.org"
  ],
  "la": [
    " Sottotitoli creati dalla comunità Amara.org",
    " Sous-titres réalisés para la communauté d'Amara.org"
  ],
  "ln": [
    " Sous-titres réalisés para la communauté d'Amara.org"
  ],
  "pl": [
    " Napisy stworzone przez społeczność Amara.org",
    " Napisy wykonane przez społeczność Amara.org",
    " Zdjęcia i napisy stworzone przez społeczność Amara.org",
    " napisy stworzone przez społeczność Amara.org",
    " Tłumaczenie i napisy stworzone przez społeczność Amara.org",
    " Napisy stworzone przez społeczności Amara.org",
    " Tłumaczenie stworzone przez społeczność Amara.org",
    " Napisy robione przez społeczność Amara.org"
    " www.multi-moto.eu",
  ],
  "ru": [
    " Редактор субтитров А.Синецкая Корректор А.Егорова"
  ],
  "tr": [
    " Yorumlarınızıza abone olmayı unutmayın.",
  ],
  "su": [
    " Sottotitoli creati dalla comunità Amara.org"
  ],
  "zh": [
    "字幕由Amara.org社区提供",
    "小編字幕由Amara.org社區提供"
  ]
}

class Transcript:
    """
    Class for storing transcript data, including speaker information and text segments, 
    and exporting it to various file formats such as JSON, HTML, and LaTeX.
    """
    
    def __init__(self, transcript: dict) -> None:
        """
        Initializes the Transcript object with the given transcript data.

        Args:
            transcript (dict): A dictionary containing the formatted transcript string.
                              Keys should correspond to segment IDs, and values should
                              contain speaker and segment information.
        """

        self.transcript = transcript
        self._remove_hallucinations()
        self.speakers = self._extract_speakers()
        self.segments = self._extract_segments()
        self.annotation = {}
    
    def annotate(self, *args, **kwargs) -> dict:
        """
        Annotates the transcript to associate specific names with speakers.

        Args:
            args (list): List of speaker names. These will be mapped sequentially to the speakers.
            kwargs (dict): Dictionary with speaker names as keys and list of segments as values.

        Returns:
            dict: Dictionary with speaker names as keys and list of segments as values.

        Raises:
            ValueError: If the number of speaker names does not match the number 
                        of speakers, or if an unknown speaker is found.
        """
        
        annotations = {}
        if args and len(args) != len(self.speakers):
            raise ValueError("Number of speaker names does not match number of speakers")
        
        if args:
            for arg, speaker in zip(args, sorted(self.speakers)):
                
                annotations[speaker] = arg
        
        invalid_speakers = set(kwargs.keys()) - set(self.speakers)
        if invalid_speakers:
            raise ValueError(f"These keys are not speakers: {', '.join(invalid_speakers)}")

        annotations.update({key: kwargs[key] for key in self.speakers if key in kwargs})

        self.annotation = annotations
        
        return self
    
    def _remove_hallucinations(self) -> None:
        segments_to_drop=[]

        for id in self.transcript:
            for language, snippets in WHISPER_HALLUCINATIONS.items():
                for snippet in snippets:
                    self.transcript[id]['text']=self.transcript[id]['text'].replace(snippet,'')
            if self.transcript[id]['text'] == '': segments_to_drop.append(id)

        for id in segments_to_drop:
            del self.transcript[id]

    def _extract_speakers(self) -> list:
        """
        Extracts the unique speaker names from the transcript.

        Returns:
            list: List of unique speaker names in the transcript.
        """
        
        return list(set([self.transcript[id]["speakers"] for id in self.transcript]))
    
    def _extract_segments(self) -> list:
        """
        Extracts all the text segments from the transcript.

        Returns:
            list: List of segments, where each segment is represented
                    by the starting and ending times.
        """
        return [self.transcript[id]["segments"] for id in self.transcript]

    def __str__(self) -> str:
        """
        Converts the transcript to a string representation.

        Returns:
            str: String representation of the transcript, including speaker names and
                time stamps for each segment.
        """
        fstring = ""
        
        for _id in self.transcript:
            seq = self.transcript[_id]
            
            if self.annotation:
                speaker = self.annotation[seq["speakers"]]
            else:
                speaker = seq["speakers"]
            
            segm = seq["segments"]
            sseg = time.strftime("%H:%M:%S",time.gmtime(segm[0]))
            eseg = time.strftime("%H:%M:%S",time.gmtime(segm[1]))
            
            fstring += f"{speaker} ({sseg} ; {eseg}):\t{seq['text']}\n"
        
        return fstring
    
    def __repr__(self) -> str:
        """Return a string representation of the Transcript object.

        Returns:
            str: A string that provides an informative description of the object.
        """
        return f"Transcript(speakers = {self.speakers},"\
                f"segments = {self.segments}, annotation = {self.annotation})"
    
    def get_dict(self) -> dict:
        """
        Get transcript as dict

        :return: transcript as dict
        :rtype: dict
        """
        
        return self.transcript
    
    def get_json(self, *args, use_annotation : bool = True, **kwargs) -> str:
        """
        Get transcript as json string
        :return: transcript as json string
        :rtype: str
        """
        if "indent" not in kwargs:
            kwargs["indent"] = 3
        
        if use_annotation and self.annotation:
            for _id in self.transcript:
                seq = self.transcript[_id]
                seq["speakers"] = self.annotation[seq["speakers"]]
            
        return json.dumps(self.transcript, *args, **kwargs)
    
    def get_html(self) -> str:
        """
        Get transcript as html string

        :return: transcript as html string
        :rtype: str
        """
        html = "<p>" + self.__str__().replace("\n", "<br>") + "</p>"
        html = "<html><body>" + html + "</body></html>"
        html = html.replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
       
        return html   
    
    def get_md(self) -> str:
        """Get transcript as Markdown string, using HTML formatting.

        Returns:
            str: Transcript as a Markdown string.
        """
        return self.get_html()
    
    def get_tex(self) -> str:
        """Get transcript as LaTeX string. If no annotations are present, the speakers will
        be annotated with the first letters of the alphabet.

        Returns:
            str: Transcript as LaTeX string.
        """
        if not self.annotation:

            self.annotate(*ALPHABET[:len(self.speakers)])
        
        fstring ="\\begin{drama}"
        
        for speaker in self.speakers:
            
            fstring += "\n\t\\Character{"+ str(self.annotation[speaker]) + "}" \
                "{"+ str(self.annotation[speaker]) + "}"
        
        for id in self.transcript:
            seq = self.transcript[id]
            speaker = self.annotation[seq["speakers"]]
            fstring += f"\n\\{speaker}speaks:\n{seq['text']}"
        
        fstring += "\n\\end{drama}"
        
        return fstring
        
            
    def to_json(self,path, *args, **kwargs) -> None:
        """Save transcript as json file
        
        Args:
            path (str): path to save file
        """
        with open(path, "w") as f:
            json.dump(self.transcript, f, *args, **kwargs)
    
    def to_txt(self, path: str) -> None:
        """Save transcript as a LaTeX file (placeholder function, implementation needed).

        Args:
            path (str): Path to save the LaTeX file.
        """
        
        with open(path, "w") as f:
            f.write(self.__str__())
    
    def to_md(self, path: str) -> None:
        """Get transcript as Markdown string, using HTML formatting.

        Returns:
            str: Transcript as a Markdown string.
        """
        return self.to_html(path)
    
    def to_html(self, path: str) -> None:
        """
        Save transcript as html file

        :param path: path to save file
        :type path: str
        """
        
        with open(path, "w") as file:
            file.write(self.get_html())
    
    def to_tex(self, path: str) -> None:
        """Save transcript as a LaTeX file (placeholder function, implementation needed).

        Args:
            path (str): Path to save the LaTeX file.
        """
        pass
    
    def to_pdf(self, path: str) -> None:
        """Save transcript as a PDF file (placeholder function, implementation needed).

        Args:
            path (str): Path to save the PDF file.
        """
        pass
    
    def save(self, path: str, *args, **kwargs) -> None:
        """Save transcript to file with the given path and file format.

        This method can save the transcript in various formats including JSON, TXT,
        MD, HTML, TEX, and PDF. The file format is determined by the extension of
        the path.

        Args:
            path (str): Path to save the file, including the desired file extension.
            *args: Additional positional arguments to be passed to the specific save methods.
            **kwargs: Additional keyword arguments to be passed to the specific save methods.

        Raises:
            ValueError: If the file format specified in the path is unknown.
        """
        
        if path.endswith(".json"):
            self.to_json(path, *args, **kwargs)
        elif path.endswith(".txt"):
            self.to_txt(path, *args, **kwargs)
        elif path.endswith(".md"):
            self.to_md(path, *args, **kwargs)
        elif path.endswith(".html"):
            self.to_html(path, *args, **kwargs)
        elif path.endswith(".tex"):
            self.to_tex(path, *args, **kwargs)
        elif path.endswith(".pdf"):
            self.to_pdf(path, *args, **kwargs)
        else:
            raise ValueError("Unknown file format")
        
    @classmethod
    def from_json(cls, json: Union[dict, str]) -> "Transcript":
        """Load transcript from json file

        Args:
            path (str): path to json file

        Returns:
            Transcript: Transcript object
        """
        if isinstance(json, dict):
            return cls(json)
        else:
            try:
                transcript = json.loads(json)
            except:
                with open(json, "r") as f:
                    transcript = json.load(f)
            
            return cls(transcript)

    