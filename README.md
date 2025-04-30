# LogicLang
The simple logical language

---

## Overview

---

## Table of Contents

<!-- TOC -->
* [LogicLang](#logiclang)
  * [Overview](#overview)
  * [Table of Contents](#table-of-contents)
  * [Description](#description)
  * [Features](#features)
  * [Setup](#setup)
  * [Limitations](#limitations)
  * [Planned Updates](#planned-updates)
  * [Screenshots](#screenshots)
  * [Syntax](#syntax)
<!-- TOC -->

---

## Description

---

## Features

---

## Setup

---

## Limitations

---

## Planned Updates

| Item                      | NS / IP / C * | Planned Release Update |
|:--------------------------|:-------------:|-----------------------:|
| Functions and Classes     |       C       |                   8a20 |
| Advanced Funcitions       |      IP       |                   9a10 |
| Arrays Fully Working      |      IP       |                   8a30 |
| Sets, Tuples, other types |      NS       |                   8a40 |
| Multithreading, etc.      |      NS       |           10a or later |


*Not Started / In Progress / Completed

```
            0a00c0
            ^ ^  ^
 Major update |  |
              |  |
   Minor update  |
                 |
    Minor change/fix
           (commit)
```


---

## Screenshots

![Image](./doc/img/img.png)

![Image](./doc/img/img_1.png)

---

## Syntax

For the logic filetype of LogicLang, syntax is pretty simple

### Environment
To start, we need to define a few things:

* We will begin the file with `name`, which will set the window title and the reference
* We will also set `*FILETYPE` to 'logic' (compound will be used later)
```
name hello_world
*FILETYPE logic
```

### Printing and Variables

IF you want to print, you can use `print text`

```
print text Hello World
```

To assign variables, we will use `general set`, which will 
be used when we don't know what type something is.

To get a variable, you surround the name of the variable with exclamation marks

Print comes with its own method of printing variables, so those wont be needed there.

Here's an example:
```
general set variable a to 10
general set variable b to !a!
print variable b
```