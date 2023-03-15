// ==UserScript==
// @name         DLWatcher
// @namespace    https://github.com/imba-tjd
// @version      0.2
// @description  This script adds Lowest label on detail pages if there are records in csv.
// @author       imba-tjd
// @homepageURL  https://github.com/imba-tjd/DLWatcher
// @license      AGPL
// @icon         https://www.dlsite.com/favicon.ico

// @grant        GM.getResourceUrl
// @match        https://www.dlsite.com/*/work/=/product_id/*
// @run-at       document-idle
// @resource     CSVDATA https://github.com/imba-tjd/DLWatcher/raw/gh-pages/data.csv
// ==/UserScript==

'use strict'

/** @param {String} url */
function parse_rj(url) {
    return url.match(/product_id\/(\w\w\d+?)\b/)?.[1]
}

/**
 * @param {String} data
 * @param {String} rj
 */
function find_line(data, rj) {
    const ndx = data.indexOf(rj)
    if (ndx == -1) return ''

    return data.slice(ndx, data.indexOf("\n", ndx))
}

/** @param {String} line */
function find_price(line) {
    const fields = line.split(",")
    if (fields.length != 5) return undefined;

    return fields[2]
}

async function get_data() {
    const url = await GM.getResourceUrl('CSVDATA')
    const data = await fetch(url)
    return await data.text()
}

function get_container() {
    return document.querySelector('#work_price .work_buy_container')
}

/**
 * @param {String} price
 * @param {String} lowest_text
 */
function create_work_buy_body(price, lowest_text = 'Lowest') {
    return `
        <div class="work_buy_body">
            <div class="work_buy_label">${lowest_text}</div>
            <div class="work_buy_content"><strong>${price} JPY</strong></div>
        </div>`
}

function get_lang() {
    const lang_li = document.querySelectorAll('.type_language li.header_dropdown_list_item')
    const lang_arr = [...lang_li]

    let ndx = 1;
    lang_arr.forEach((el, i) => {
        if (el.classList.contains('is-selected')) ndx = i
    })

    return ['ja', 'en', 'cn', 'tw', 'ko'][ndx]
}

async function main() {
    const url = document.URL
    const rj = parse_rj(url)
    if (typeof rj === 'undefined') return

    const data = await get_data()

    const line = find_line(data, rj)
    const price = find_price(line)
    if (typeof price === 'undefined') return

    const lang = get_lang()
    const lowest_text = lang === 'cn' ? '最低价' : 'Lowest'

    const body = create_work_buy_body(price, lowest_text)

    while(!document.querySelector('#work_buy_btn .btn_buy'))
        await new Promise((resolve, _) => setTimeout(resolve, 1000))

    get_container()?.insertAdjacentHTML("beforeend", body)
}

main()
