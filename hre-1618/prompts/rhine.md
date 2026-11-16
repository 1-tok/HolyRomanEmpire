# HRE 1618: Rhine sprite prompts

Paste the standing instructions (style, format, historical rules) into the ChatGPT project once. Then send one prompt below per sprite, in order from Basel down to Utrecht. Save each result as the file named above its prompt, move it to `sprites/inbox/`, and run `python3 tools/ingest_sprites.py --commit --push`.

River courses were measured from the Natural Earth Rhine centreline on the same projection as the base map (north is up on the sheet), by `tools/river_course.py`. "Enters" and "leaves" are the edges (or corners, for diagonal courses) of the square canvas where the river crosses it, in the direction of flow. The Rhine flows from Basel to the sea, so each sprite's river leaves where the next sprite's river enters, as nearly as the course allows.

Special cases: at Arnhem and Nijmegen the Rhine has split, and the sprites show the Nederrijn and the Waal. At Utrecht the main channel is the Old Rhine. Basel and Cologne have the Rhine at the foot of the old town.

## 1. Basel

File: `Basel.png`

> Hand-drawn vignette of Basel as it stood in 1618: the Minster with its two towers on the left bank, the stone Rhine bridge, a walled Swiss city. The Rhine flows north-west, entering the square at its bottom-right corner and leaving at its top-left corner. It runs close beside the buildings, on the north-east side of the city. Transparent PNG, square, no text.

## 2. Strasbourg

File: `Strasbourg.png`

> Hand-drawn vignette of Strasbourg as it stood in 1618: the Münster with its completed Gothic spire, half-timbered houses, city walls and the Ill canals. The Rhine flows north, entering the square at its bottom edge and leaving at its top edge. It runs a short way from the buildings, along the east side of the square. Transparent PNG, square, no text.

## 3. Speyer

File: `Speyer.png`

> Hand-drawn vignette of Speyer as it stood in 1618: the Romanesque imperial cathedral with its four towers, walls and gates. The Rhine flows north, entering the square at its bottom edge and leaving at its top edge. It runs a short way from the buildings, along the east side of the square. Transparent PNG, square, no text.

## 4. Worms

File: `Worms.png`

> Hand-drawn vignette of Worms as it stood in 1618: the Romanesque Dom St Peter with its towers, city walls and gates. The Rhine flows north, entering the square at its bottom edge and leaving at its top edge. It runs close beside the buildings, on the east side of the city. Transparent PNG, square, no text.

## 5. Mainz

File: `Mainz.png`

> Hand-drawn vignette of Mainz as it stood in 1618: the cathedral with its Romanesque towers, the Electoral palace, the city walls, the Rhine port. The Rhine flows north-west, entering the square at its bottom-right corner and leaving at its top-left corner. It passes close by the foot of the buildings. Transparent PNG, square, no text.

## 6. Koblenz

File: `Koblenz.png`

> Hand-drawn vignette of Koblenz as it stood in 1618: the Electoral palace and the old castle at the meeting of the Moselle and the Rhine, with the Ehrenbreitstein fortress on the far rock. The Rhine flows north, entering the square at its bottom edge and leaving at its top edge. It passes close by the foot of the buildings. Transparent PNG, square, no text.

## 7. Bonn

File: `Bonn.png`

> Hand-drawn vignette of Bonn as it stood in 1618: the Romanesque Minster with its towers, the town walls and the Electoral palace, a small Rhine port. The Rhine flows north-west, entering the square at its bottom-right corner and leaving at its top-left corner. It runs close beside the buildings, on the north-east side of the city. Transparent PNG, square, no text.

## 8. Cologne

File: `Cologne.png`

> Hand-drawn vignette of Cologne as it stood in 1618: the Gothic Dom unfinished, with its stump of a tower and a wooden crane on top, Great St Martin, Roman walls with gates, the Rhine port. The Rhine flows north, entering the square at its bottom edge and leaving at its top edge. It passes close by the foot of the buildings. Transparent PNG, square, no text.

## 9. Düsseldorf

File: `Düsseldorf.png`

> Hand-drawn vignette of Düsseldorf as it stood in 1618: the small ducal castle and tower, the walls and the town church, a Rhine port. The Rhine flows north, entering the square at its bottom edge and leaving at its top edge. It runs close beside the buildings, on the west side of the city. Transparent PNG, square, no text.

## 10. Duisburg

File: `Duisburg.png`

> Hand-drawn vignette of Duisburg as it stood in 1618: a small walled market town with the St Salvator church, the Ruhr mouth, a Rhine harbour. The Rhine flows north, entering the square at its bottom edge and leaving at its top edge. It runs a short way from the buildings, along the west side of the square. Transparent PNG, square, no text.

## 11. Wesel

File: `Wesel.png`

> Hand-drawn vignette of Wesel as it stood in 1618: a strong walled fortress town at the mouth of the Lippe, with its large Gothic church and bastions. The Rhine flows north-west, entering the square at its bottom-right corner and leaving at its top-left corner. It runs a short way from the buildings, along the south-west side of the square. Transparent PNG, square, no text.

## 12. Arnhem

File: `Arnhem.png`

> Hand-drawn vignette of Arnhem as it stood in 1618: the Gothic church of St Eusebius with its tall tower, the town walls, a river port on the Nederrijn. The Nederrijn (the Rhine's northern branch) flows west, entering the square at its right edge and leaving at its left edge. It runs close beside the buildings, on the south side of the city. Transparent PNG, square, no text.

## 13. Nijmegen

File: `Nijmegen.png`

> Hand-drawn vignette of Nijmegen as it stood in 1618: the St Stevenskerk with its tower and the Valkhof castle hill above the Waal, with its town walls. The Waal (the Rhine's main branch) flows west, entering the square at its right edge and leaving at its left edge. It runs close beside the buildings, on the north side of the city. Transparent PNG, square, no text.

## 14. Utrecht

File: `Utrecht.png`

> Hand-drawn vignette of Utrecht as it stood in 1618: the Dom with its tall Gothic tower, rows of canal houses, the Old Rhine channel running through the city. The Old Rhine channel flows west through the middle of the city, entering the square at its right edge and leaving at its left edge. Transparent PNG, square, no text.
