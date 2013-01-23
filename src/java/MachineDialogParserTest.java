/*
 * otopi -- plugable installer
 * Copyright (C) 2012-2013 Red Hat, Inc.
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
 */
package org.ovirt.otopi.dialog;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.OutputStream;
import java.io.UnsupportedEncodingException;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import org.junit.Test;

public class MachineDialogParserTest {

	private MachineDialogParser getParser(String stream, OutputStream os) throws UnsupportedEncodingException {
		MachineDialogParser parser = new MachineDialogParser();
		parser.setStreams(
			new ByteArrayInputStream(stream.getBytes("UTF-8")),
			os
		);
		return parser;
	}

	@Test
	public void testBasic() throws Exception {
		String incoming = (
			"***TERMINATE\n"
		);
		String expected_outgoing = (
			""
		);
		ByteArrayOutputStream bos = new ByteArrayOutputStream();
		MachineDialogParser parser = getParser(incoming, bos);

		Event.Base bevent;

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.Terminate);

		assertEquals(expected_outgoing, new String(bos.toByteArray(), "UTF-8"));
	}

	@Test(expected=RuntimeException.class)
	public void testInvalidToken1() throws Exception {
		String incoming = (
			"XXX\n"
		);
		MachineDialogParser parser = getParser(incoming, new ByteArrayOutputStream());
		Event.Base bevent;
		bevent = parser.nextEvent();
	}

	@Test(expected=RuntimeException.class)
	public void testInvalidToken2() throws Exception {
		String incoming = (
			"***Q:STRING1 str1\n"
		);
		MachineDialogParser parser = getParser(incoming, new ByteArrayOutputStream());
		Event.Base bevent;
		bevent = parser.nextEvent();
	}

	@Test(expected=RuntimeException.class)
	public void testInvalidToken3() throws Exception {
		String incoming = (
			"***Q:MUTLI-STRING str1\n"
		);
		MachineDialogParser parser = getParser(incoming, new ByteArrayOutputStream());
		Event.Base bevent;
		bevent = parser.nextEvent();
	}

	@Test
	public void testCoverage() throws Exception {
		String incoming = (
			"#NOTE\n" +
			"#NOTE\n" +
			"***L:INFO log record\n" +
			"***L:WARNING log record\n" +
			"***L:ERROR log record\n" +
			"***L:CRITICAL log record\n" +
			"***L:FATAL log record\n" +
			"#INFO\n" +
			"***Q:STRING str1\n" +	// 1
			"***Q:MULTI-STRING mstr0 boundary1 boundary2\n" + // 2
			"***Q:MULTI-STRING mstr1 boundary1 boundary2\n" + // 3
			"***Q:MULTI-STRING mstr2 boundary1 boundary2\n" + // 4
			"***Q:VALUE value0\n" +	// 5
			"***Q:VALUE value1\n" +	// 6
			"***Q:VALUE value2\n" +	// 7
			"***Q:VALUE value3\n" +	// 8
			"***Q:VALUE value4\n" +	// 9
			"***Q:VALUE value5\n" +	// 10
			"***D:VALUE value10=none:NoneType\n" +
			"***D:VALUE value11=bool:True\n" +
			"***D:VALUE value12=bool:False\n" +
			"***D:VALUE value13=int:52\n" +
			"***D:VALUE value14=str:value 2\n" +
			"***D:MULTI-STRING mstr3 boundary2\n" +
			"line 1\n" +
			"line 2\n" +
			"boundary2\n" +
			"***CONFIRM confirm0 description 0\n" +	// 11
			"***CONFIRM confirm1 description 1\n" +	// 12
			"***CONFIRM confirm2 description 1\n" +	// 13
			"***TERMINATE\n" +
			""
		);
		String expected_outgoing = (
			"value 1\n" +		// 1
			"boundary2\n" +		// 2
			"line 1\n" +		// 3
			"line 2\n" +
			"boundary1\n" +
			"boundary1\n" +		// 4
			"ABORT value0\n" +	// 5
			"VALUE value1=none:null\n" +	// 6
			"VALUE value2=bool:true\n" +	// 7
			"VALUE value3=bool:false\n" +	// 8
			"VALUE value4=int:47\n" +	// 9
			"VALUE value5=str:string 1\n" + // 10
			"ABORT confirm0\n" +		// 11
			"CONFIRM confirm1=no\n" +	// 12
			"CONFIRM confirm2=yes\n" +	// 13
			""
		);
		ByteArrayOutputStream bos = new ByteArrayOutputStream();
		MachineDialogParser parser = getParser(incoming, bos);

		Event.Base bevent;
		Event.Log logevent;
		Event.QueryString querystringevent;
		Event.QueryMultiString querymultistringevent;
		Event.QueryValue queryvalueevent;
		Event.DisplayValue displayvalueevent;
		Event.DisplayMultiString displaymultistringvalue;
		Event.Confirm confirmevent;

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.Log);
		logevent = (Event.Log)bevent;
		assertEquals(Event.Log.Severity.INFO, logevent.severity);
		assertEquals("log record", logevent.record);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.Log);
		logevent = (Event.Log)bevent;
		assertEquals(Event.Log.Severity.WARNING, logevent.severity);
		assertEquals("log record", logevent.record);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.Log);
		logevent = (Event.Log)bevent;
		assertEquals(Event.Log.Severity.ERROR, logevent.severity);
		assertEquals("log record", logevent.record);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.Log);
		logevent = (Event.Log)bevent;
		assertEquals(Event.Log.Severity.CRITICAL, logevent.severity);
		assertEquals("log record", logevent.record);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.Log);
		logevent = (Event.Log)bevent;
		assertEquals(Event.Log.Severity.FATAL, logevent.severity);
		assertEquals("log record", logevent.record);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryString);
		querystringevent = (Event.QueryString)bevent;
		assertEquals("str1", querystringevent.name);
		querystringevent.value = "value 1";
		parser.sendResponse(querystringevent);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryMultiString);
		querymultistringevent = (Event.QueryMultiString)bevent;
		assertEquals("mstr0", querymultistringevent.name);
		querymultistringevent.abort = true;
		parser.sendResponse(querymultistringevent);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryMultiString);
		querymultistringevent = (Event.QueryMultiString)bevent;
		assertEquals("mstr1", querymultistringevent.name);
		querymultistringevent.value = new String[] {"line 1", "line 2"};
		parser.sendResponse(querymultistringevent);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryMultiString);
		querymultistringevent = (Event.QueryMultiString)bevent;
		assertEquals("mstr2", querymultistringevent.name);
		querymultistringevent.value = new String[0];
		parser.sendResponse(querymultistringevent);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryValue);
		queryvalueevent = (Event.QueryValue)bevent;
		assertEquals("value0", queryvalueevent.name);
		queryvalueevent.abort = true;
		parser.sendResponse(queryvalueevent);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryValue);
		queryvalueevent = (Event.QueryValue)bevent;
		assertEquals("value1", queryvalueevent.name);
		queryvalueevent.value = null;
		parser.sendResponse(queryvalueevent);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryValue);
		queryvalueevent = (Event.QueryValue)bevent;
		assertEquals("value2", queryvalueevent.name);
		queryvalueevent.value = new Boolean(true);
		parser.sendResponse(queryvalueevent);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryValue);
		queryvalueevent = (Event.QueryValue)bevent;
		assertEquals("value3", queryvalueevent.name);
		queryvalueevent.value = new Boolean(false);
		parser.sendResponse(queryvalueevent);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryValue);
		queryvalueevent = (Event.QueryValue)bevent;
		assertEquals("value4", queryvalueevent.name);
		queryvalueevent.value = new Integer(47);
		parser.sendResponse(queryvalueevent);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryValue);
		queryvalueevent = (Event.QueryValue)bevent;
		assertEquals("value5", queryvalueevent.name);
		queryvalueevent.value = "string 1";
		parser.sendResponse(queryvalueevent);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.DisplayValue);
		displayvalueevent = (Event.DisplayValue)bevent;
		assertEquals("value10", displayvalueevent.name);
		assertEquals(null, displayvalueevent.value);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.DisplayValue);
		displayvalueevent = (Event.DisplayValue)bevent;
		assertEquals("value11", displayvalueevent.name);
		assertEquals(new Boolean(true), displayvalueevent.value);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.DisplayValue);
		displayvalueevent = (Event.DisplayValue)bevent;
		assertEquals("value12", displayvalueevent.name);
		assertEquals(new Boolean(false), displayvalueevent.value);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.DisplayValue);
		displayvalueevent = (Event.DisplayValue)bevent;
		assertEquals("value13", displayvalueevent.name);
		assertEquals(new Integer(52), displayvalueevent.value);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.DisplayValue);
		displayvalueevent = (Event.DisplayValue)bevent;
		assertEquals("value14", displayvalueevent.name);
		assertEquals("value 2", displayvalueevent.value);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.DisplayMultiString);
		displaymultistringvalue = (Event.DisplayMultiString)bevent;
		assertEquals("mstr3", displaymultistringvalue.name);
		assertArrayEquals(new String[] {"line 1", "line 2"}, displaymultistringvalue.value);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.Confirm);
		confirmevent = (Event.Confirm)bevent;
		assertEquals("confirm0", confirmevent.what);
		assertEquals("description 0", confirmevent.description);
		confirmevent.abort = true;
		parser.sendResponse(confirmevent);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.Confirm);
		confirmevent = (Event.Confirm)bevent;
		assertEquals("confirm1", confirmevent.what);
		assertEquals("description 1", confirmevent.description);
		parser.sendResponse(confirmevent);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.Confirm);
		confirmevent = (Event.Confirm)bevent;
		assertEquals("confirm2", confirmevent.what);
		assertEquals("description 1", confirmevent.description);
		confirmevent.reply = true;
		parser.sendResponse(confirmevent);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.Terminate);

		assertEquals(expected_outgoing, new String(bos.toByteArray(), "UTF-8"));
	}

	@Test
	public void testLog() throws Exception {
		String incoming = (
			"***Q:STRING prompt\n" +
			"***D:MULTI-STRING log boundary1\n" +
			"line 1\n" +
			"line 2\n" +
			"boundary1\n" +
			"***TERMINATE\n" +
			""
		);
		String expected_outgoing = (
			"log\n" +
			""
		);
		ByteArrayOutputStream bos = new ByteArrayOutputStream();
		MachineDialogParser parser = getParser(incoming, bos);

		Event.Base bevent;
		Event.QueryString querystringevent;

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryString);
		querystringevent = (Event.QueryString)bevent;
		assertEquals("prompt", querystringevent.name);
		ByteArrayOutputStream log = new ByteArrayOutputStream();
		parser.cliDownloadLog(log);
		assertEquals("line 1\nline 2\n", new String(log.toByteArray(), "UTF-8"));

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.Terminate);

		assertEquals(expected_outgoing, new String(bos.toByteArray(), "UTF-8"));
	}

	@Test
	public void testEnvGet() throws Exception {
		String incoming = (
			"***Q:STRING prompt\n" +
			"***D:VALUE key1=str:value1\n" +
			"***Q:STRING prompt\n" +
			"***D:MULTI-STRING key2 boundary1\n" +
			"line 1\n" +
			"line 2\n" +
			"boundary1\n" +
			"***TERMINATE\n" +
			""
		);
		String expected_outgoing = (
			"env-get -k key1\n" +
			"env-get -k key2\n" +
			""
		);
		ByteArrayOutputStream bos = new ByteArrayOutputStream();
		MachineDialogParser parser = getParser(incoming, bos);

		Event.Base bevent;
		Event.QueryString querystringevent;
		Object value;

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryString);
		querystringevent = (Event.QueryString)bevent;
		assertEquals("prompt", querystringevent.name);
		value = parser.cliEnvironmentGet("key1");
		assertEquals("value1", value);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryString);
		querystringevent = (Event.QueryString)bevent;
		assertEquals("prompt", querystringevent.name);
		value = parser.cliEnvironmentGet("key2");
		assertTrue(value instanceof String[]);
		assertArrayEquals(new String [] {"line 1", "line 2"}, (String[])value);

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.Terminate);

		assertEquals(expected_outgoing, new String(bos.toByteArray(), "UTF-8"));
	}

	@Test
	public void testEnvSet() throws Exception {
		String incoming = (
			"***Q:STRING prompt\n" +
			"***Q:VALUE key1\n" +
			"***Q:STRING prompt\n" +
			"***Q:MULTI-STRING key2 boundary1 boundary2\n" +
			"***TERMINATE\n" +
			""
		);
		String expected_outgoing = (
			"env-query -k key1\n" +
			"VALUE key1=str:value 1\n" +
			"env-query-multi -k key2\n" +
			"line 1\n" +
			"line 2\n" +
			"boundary1\n" +
			""
		);
		ByteArrayOutputStream bos = new ByteArrayOutputStream();
		MachineDialogParser parser = getParser(incoming, bos);

		Event.Base bevent;
		Event.QueryString querystringevent;

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryString);
		querystringevent = (Event.QueryString)bevent;
		assertEquals("prompt", querystringevent.name);
		parser.cliEnvironmentSet("key1", "value 1");

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryString);
		querystringevent = (Event.QueryString)bevent;
		assertEquals("prompt", querystringevent.name);
		parser.cliEnvironmentSet("key2", new String[] {"line 1", "line 2"});

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.Terminate);

		assertEquals(expected_outgoing, new String(bos.toByteArray(), "UTF-8"));
	}

	@Test(expected=IllegalArgumentException.class)
	public void testEnvSetInvalidType() throws Exception {
		String incoming = (
			"***Q:STRING prompt\n" +
			"***Q:VALUE key1\n" +
			""
		);
		String expected_outgoing = (
			"env-query -k key1\n" +
			""
		);
		ByteArrayOutputStream bos = new ByteArrayOutputStream();
		MachineDialogParser parser = getParser(incoming, bos);

		Event.Base bevent;
		Event.QueryString querystringevent;

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryString);
		querystringevent = (Event.QueryString)bevent;
		assertEquals("prompt", querystringevent.name);
		parser.cliEnvironmentSet("key1", this);
	}

	@Test(expected=IllegalArgumentException.class)
	public void testEnvSetInvalidString() throws Exception {
		String incoming = (
			"***Q:STRING prompt\n" +
			"***Q:VALUE key1\n" +
			""
		);
		String expected_outgoing = (
			"env-query -k key1\n" +
			""
		);
		ByteArrayOutputStream bos = new ByteArrayOutputStream();
		MachineDialogParser parser = getParser(incoming, bos);

		Event.Base bevent;
		Event.QueryString querystringevent;

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryString);
		querystringevent = (Event.QueryString)bevent;
		assertEquals("prompt", querystringevent.name);
		parser.cliEnvironmentSet("key1", "test\nwith new line");
	}

	@Test
	public void testMiscCLI() throws Exception {
		String incoming = (
			"***Q:STRING prompt\n" +
			"***Q:STRING prompt\n" +
			"***Q:STRING prompt\n" +
			"***Q:STRING prompt\n" +
			"***TERMINATE\n" +
			""
		);
		String expected_outgoing = (
			"install\n" +
			"quit\n" +
			"abort\n" +
			"noop\n" +
			""
		);
		ByteArrayOutputStream bos = new ByteArrayOutputStream();
		MachineDialogParser parser = getParser(incoming, bos);

		Event.Base bevent;
		Event.QueryString querystringevent;

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryString);
		querystringevent = (Event.QueryString)bevent;
		assertEquals("prompt", querystringevent.name);
		parser.cliInstall();

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryString);
		querystringevent = (Event.QueryString)bevent;
		assertEquals("prompt", querystringevent.name);
		parser.cliQuit();

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryString);
		querystringevent = (Event.QueryString)bevent;
		assertEquals("prompt", querystringevent.name);
		parser.cliAbort();

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.QueryString);
		querystringevent = (Event.QueryString)bevent;
		assertEquals("prompt", querystringevent.name);
		parser.cliNoop();

		bevent = parser.nextEvent();
		assertTrue(bevent instanceof Event.Terminate);

		assertEquals(expected_outgoing, new String(bos.toByteArray(), "UTF-8"));
	}
}
