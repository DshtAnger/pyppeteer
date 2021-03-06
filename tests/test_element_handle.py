#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import unittest

from syncer import sync

from pyppeteer.errors import ElementHandleError

from .base import BaseTestCase


class TestBoundingBox(BaseTestCase):
    @sync
    async def test_bounding_box(self):
        await self.page.setViewport({'width': 500, 'height': 500})
        await self.page.goto(self.url + 'static/grid.html')
        elementHandle = await self.page.J('.box:nth-of-type(13)')
        box = await elementHandle.boundingBox()
        self.assertEqual({'x': 100, 'y': 50, 'width': 50, 'height': 50}, box)

    @sync
    async def test_nested_frame(self):
        await self.page.setViewport({'width': 500, 'height': 500})
        await self.page.goto(self.url + 'static/nested-frames.html')
        nestedFrame = self.page.frames[1].childFrames[1]
        elementHandle = await nestedFrame.J('div')
        box = await elementHandle.boundingBox()
        # Frame size is unstable
        # Frame order is unstable
        # self.assertIn(box, [
        #     {'x': 28, 'y': 28, 'width': 264, 'height': 16},
        #     {'x': 28, 'y': 260, 'width': 264, 'height': 16},
        # ])
        self.assertEqual(box['x'], 28)
        self.assertIn(box['y'], [28, 260])
        self.assertEqual(box['width'], 264)

    @sync
    async def test_invisible_element(self):
        await self.page.setContent('<div style="display: none;">hi</div>')
        element = await self.page.J('div')
        self.assertIsNone(await element.boundingBox())


class TestClick(BaseTestCase):
    @sync
    async def test_clik(self):
        await self.page.goto(self.url + 'static/button.html')
        button = await self.page.J('button')
        await button.click()
        self.assertEqual(await self.page.evaluate('result'), 'Clicked')

    @sync
    async def test_chadow_dom(self):
        await self.page.goto(self.url + 'static/shadow.html')
        button = await self.page.evaluateHandle('() => button')
        await button.click()
        self.assertTrue(await self.page.evaluate('clicked'))

    @sync
    async def test_text_node(self):
        await self.page.goto(self.url + 'static/button.html')
        buttonTextNode = await self.page.evaluateHandle(
            '() => document.querySelector("button").firstChild')
        with self.assertRaises(ElementHandleError) as cm:
            await buttonTextNode.click()
        self.assertEqual('Node is not of type HTMLElement',
                         cm.exception.args[0])

    @sync
    async def test_detached_node(self):
        await self.page.goto(self.url + 'static/button.html')
        button = await self.page.J('button')
        await self.page.evaluate('btn => btn.remove()', button)
        with self.assertRaises(ElementHandleError) as cm:
            await button.click()
        self.assertEqual('Node is detached from document',
                         cm.exception.args[0])

    @sync
    async def test_hidden_node(self):
        await self.page.goto(self.url + 'static/button.html')
        button = await self.page.J('button')
        await self.page.evaluate('btn => btn.style.display = "none"', button)
        with self.assertRaises(ElementHandleError) as cm:
            await button.click()
        self.assertEqual('Node is not visible.', cm.exception.args[0])

    @sync
    async def test_recursively_hidden_node(self):
        await self.page.goto(self.url + 'static/button.html')
        button = await self.page.J('button')
        await self.page.evaluate(
            'btn => btn.parentElement.style.display = "none"', button)
        with self.assertRaises(ElementHandleError) as cm:
            await button.click()
        self.assertEqual('Node is not visible.', cm.exception.args[0])

    @sync
    async def test_br_node(self):
        await self.page.setContent('hello<br>goodbye')
        br = await self.page.J('br')
        with self.assertRaises(ElementHandleError) as cm:
            await br.click()
        self.assertEqual('Node is not visible.', cm.exception.args[0])


class TestHover(BaseTestCase):
    @sync
    async def test_hover(self):
        await self.page.goto(self.url + 'static/scrollable.html')
        button = await self.page.J('#button-6')
        await button.hover()
        self.assertEqual(
            await self.page.evaluate(
                'document.querySelector("button:hover").id'),
            'button-6'
        )


@unittest.skip('Screenshot tests are not implemented')
class TestScreenshot(BaseTestCase):
    pass


class TestQuerySelector(BaseTestCase):
    @sync
    async def test_element_handle_J(self):
        await self.page.setContent('''
<html><body><div class="second"><div class="inner">A</div></div></body></html>
        ''')
        html = await self.page.J('html')
        second = await html.J('.second')
        inner = await second.J('.inner')
        content = await self.page.evaluate('e => e.textContent', inner)
        self.assertEqual(content, 'A')

    @sync
    async def test_element_handle_J_none(self):
        await self.page.setContent('''
<html><body><div class="second"><div class="inner">A</div></div></body></html>
        ''')
        html = await self.page.J('html')
        second = await html.J('.third')
        self.assertIsNone(second)

    @sync
    async def test_element_handle_JJ(self):
        await self.page.setContent('''
<html><body><div>A</div><br/><div>B</div></body></html>
        ''')
        html = await self.page.J('html')
        elements = await html.JJ('div')
        self.assertEqual(len(elements), 2)
        if sys.version_info >= (3, 6):
            result = []
            for elm in elements:
                result.append(
                    await self.page.evaluate('(e) => e.textContent', elm)
                )
            self.assertEqual(result, ['A', 'B'])

    @sync
    async def test_element_handle_JJ_empty(self):
        await self.page.setContent('''
<html><body><span>A</span><br/><span>B</span></body></html>
        ''')
        html = await self.page.J('html')
        elements = await html.JJ('div')
        self.assertEqual(len(elements), 0)

    @sync
    async def test_element_handle_xpath(self):
        await self.page.setContent(
            '<html><body><div class="second"><div class="inner">A</div></div></body></html>'  # noqa: E501
        )
        html = await self.page.querySelector('html')
        second = await html.xpath('./body/div[contains(@class, \'second\')]')
        inner = await second[0].xpath('./div[contains(@class, \'inner\')]')
        content = await self.page.evaluate('(e) => e.textContent', inner[0])
        self.assertEqual(content, 'A')

    @sync
    async def test_element_handle_xpath_not_found(self):
        await self.page.goto(self.url + 'empty')
        html = await self.page.querySelector('html')
        element = await html.xpath('/div[contains(@class, \'third\')]')
        self.assertEqual(element, [])
