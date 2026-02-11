# Arena-Star
Základní nápad

Jednoduchá dungeon crawl, rogue-light hra ve 2D pixelové grafice, hraná z ptačí
perspektivy. Hráč by si na začátku hry zbraň, případně nějaké spelly. Po spuštění by byl
hozený do dungeonu ve kterém by na něj čekali nepřátelé, odměny (např. ve formě nových
zbraní) a potenciálně i bossové. Hra by neměla přímý cíl, hráč by hrál dokud by nezemřel.

Implementace

Hra vygeneruje dungeon a v něm místnosti náhodně. Jejich počet bude konečný ale
množství náhodné a rozmístění také. Něco na styl The Binding of Isaac nebo Soul Knight.
Místnosti budou brány ze seznamu a byli by tříděné na tři typy.
1. Prázdné místnosti - můžou být prázdné kompletně nebo se v nich může nacházet
nějaký loot.
2. Místnosti s nepřáteli - nejčastější typ místnosti. Jsou v ní vždy enemáci na poražení.
3. Boss místnost - málo častá, zaručeně obsahuje bosse
Strategie hry by spočívala ve vybrání správného “gearu” (kombinace spellu a zbraně) a v
jeho následném použití.

Interface

Hlavní menu: Možnost zobrazit veškeré vybavení co hráč má a následně vybrat nebo koupit.
Hra samotná: Na obrazovce by byli vidět životy hráče a případně cooldown jeho schopností
(spellů).

Knihovny

Hra by využívala Pygame.

Veškeré informace napsané nahoře jsou stále ve fázi vývoje a konečný výsledek může jejich
uplatnění změnit nebo kompletně odstranit - vše je tedy subject to change.
