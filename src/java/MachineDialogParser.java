/*
 * otopi -- plugable installer
 * Copyright (C) 2012 Red Hat, Inc.
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

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.nio.charset.Charset;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;

import org.ovirt.otopi.dialog.constants.DialogMachineConst;
import org.ovirt.otopi.constants.Types;

/**
 * Machine dialog parser.
 *
 * Please refer to README.dialog.
 */
public class MachineDialogParser {

    private static final int BUFFER_SIZE = 10 * 1024;

    private static final Log log = LogFactory.getLog(MachineDialogParser.class);

    private static Map<String, Event.Log.Severity> LOG_SEVERITIES;
    static {
        LOG_SEVERITIES = new HashMap<String, Event.Log.Severity>();
        LOG_SEVERITIES.put(DialogMachineConst.LOG_INFO, Event.Log.Severity.INFO);
        LOG_SEVERITIES.put(DialogMachineConst.LOG_WARNING, Event.Log.Severity.WARNING);
        LOG_SEVERITIES.put(DialogMachineConst.LOG_ERROR, Event.Log.Severity.ERROR);
        LOG_SEVERITIES.put(DialogMachineConst.LOG_CRITICAL, Event.Log.Severity.CRITICAL);
        LOG_SEVERITIES.put(DialogMachineConst.LOG_FATAL, Event.Log.Severity.FATAL);
    }

    private BufferedReader _incoming;
    private PrintWriter _outgoing;

    private Event.Base _parseRequest(String request, OutputStream out) throws Exception {
        Event.Base bevent = null;

        if (request.startsWith(DialogMachineConst.LOG_PREFIX)) {
            Event.Log event;
            bevent = event = new Event.Log();
            String s[] = request.split(" ", 2);
            event.severity = LOG_SEVERITIES.get(s[0]);
            event.record = s[1];
        }
        else if (request.startsWith(DialogMachineConst.QUERY_STRING + " ")) {
            Event.QueryString event;
            bevent = event = new Event.QueryString();
            String s[] = request.split(" ", 2);
            event.name = s[1];
        }
        else if (request.startsWith(DialogMachineConst.QUERY_MULTI_STRING + " ")) {
            Event.QueryMultiString event;
            bevent = event = new Event.QueryMultiString();
            String s[] = request.split(" ", 4);
            event.name = s[1];
            event.boundary = s[2];
            event.abortboundary = s[3];
        }
        else if (request.startsWith(DialogMachineConst.QUERY_VALUE + " ")) {
            Event.QueryValue event;
            bevent = event = new Event.QueryValue();
            String s[] = request.split(" ", 2);
            event.name = s[1];
        }
        else if (request.startsWith(DialogMachineConst.DISPLAY_VALUE + " ")) {
            Event.DisplayValue event;
            bevent = event = new Event.DisplayValue();
            String s[] = request.split(" ", 2);
            String var[] = s[1].split("=", 2);
            event.name = var[0];
            String val[] = var[1].split(":", 2);
            event.type = val[0];
            String value = val[1];
            if (Types.NONE.equals(event.type)) {
                event.value = null;
            }
            else if (Types.BOOLEAN.equals(event.type)) {
                if (
                    "FALSE".equals(value) ||
                    "False".equals(value) ||
                    "F".equals(value)
                ) {
                    event.value = new Boolean(false);
                }
                else {
                    event.value = new Boolean(true);
                }
            }
            else if (Types.INTEGER.equals(event.type)) {
                event.value = new Integer(value);
            }
            else if (Types.STRING.equals(event.type)) {
                event.value = value;
            }
            else {
                throw new SoftError(
                    String.format("Invalid variable type '%1$s'", event.type)
                );
            }
        }
        else if (request.startsWith(DialogMachineConst.DISPLAY_MULTI_STRING + " ")) {
            Event.DisplayMultiString event;
            bevent = event = new Event.DisplayMultiString();
            String s[] = request.split(" ", 3);
            event.name = s[1];
            event.boundary = s[2];
            log.debug("in-request reading multi-string");
            List<String> list = new LinkedList<String>();
            String l;
            boolean done = false;
            while (
                !done &&
                (l = _incoming.readLine()) != null
            ) {
                if (event.boundary.equals(l)) {
                    done = true;
                }
                else {
                    if (out != null) {
                        out.write((l+"\n").getBytes("UTF-8"));
                    }
                    else {
                        list.add(l);
                    }
                }
            }
            event.value = list.toArray(new String[0]);
        }
        else if (request.startsWith(DialogMachineConst.CONFIRM + " ")) {
            Event.Confirm event;
            bevent = event = new Event.Confirm();
            String s[] = request.split(" ", 3);
            event.what = s[1];
            event.description = s[2];
        }
        else if (request.equals(DialogMachineConst.TERMINATE)) {
            Event.Terminate event;
            bevent = event = new Event.Terminate();
        }
        else {
            throw new RuntimeException(
                String.format(
                    "Unsupported command '%1$s'",
                    request.split(" ")[0]
                )
            );
        }

        return bevent;
    }

    /**
     * Set the dialog streams.
     * @param incoming incoming stream.
     * @param outgoing outgoing stream.
     */
    public void setStreams(InputStream incoming, OutputStream outgoing) {
        _incoming = incoming == null ? null : new BufferedReader(
            new InputStreamReader(
                incoming,
                Charset.forName("UTF-8")
            ),
            BUFFER_SIZE
        );
        _outgoing = outgoing == null ? null : new PrintWriter(
            new OutputStreamWriter(
                outgoing,
                Charset.forName("UTF-8")
            ),
            true
        );
    }

    /**
     * env-get command.
     * @param name variable name.
     * @return variable value (null, Integer, String, String[])
     */
    public Object cliEnvironmentGet(String name) throws IOException {
        Object value = null;

        log.debug(String.format("env-get %1$s", name));

        _outgoing.printf(
            "env-get -k %1$s\n",
            name
        );

        Event.Base bevent = nextEvent();
        if (bevent instanceof Event.DisplayValue) {
            Event.DisplayValue event = (Event.DisplayValue)bevent;
            value = event.value;
        }
        else if (bevent instanceof Event.DisplayMultiString) {
            Event.DisplayMultiString event = (Event.DisplayMultiString)bevent;
            value = event.value;
        }
        else {
            throw new SoftError(
                String.format(
                    "Unexpected event %s",
                    bevent
                )
            );
        }

        log.debug(
            String.format(
                "env-get %1$s=%2$s:%3$s",
                name,
                value.getClass().getName(),
                value
            )
        );

        return value;
    }

    /**
     * env-set command.
     * @param name variable name.
     * @param value value to set, type of object is attached (null, Integer, String, String[]).
     */
    public void cliEnvironmentSet(String name, Object value) throws IOException {
        log.debug(
            String.format(
                "env-query %1$s=%2$s:%3$s",
                name,
                value.getClass().getName(),
                value
            )
        );

        if (value instanceof String[]) {
            _outgoing.printf(
                "env-query-multi -k %1$s\n",
                name
            );
        }
        else {
            _outgoing.printf(
                "env-query -k %1$s\n",
                name
            );
        }

        Event.Base bevent = nextEvent();
        if (bevent instanceof Event.QueryValue) {
            Event.QueryValue event = (Event.QueryValue)bevent;
            event.value = value;
            sendResponse(event);
        }
        else if (bevent instanceof Event.QueryMultiString) {
            Event.QueryMultiString event = (Event.QueryMultiString)bevent;
            event.value = (String[])value;
            sendResponse(event);
        }
        else {
            throw new SoftError(
                String.format(
                    "Unexpected event %s",
                    bevent
                )
            );
        }
    }

    /**
     * log command.
     * @param out stream to write log into.
     */
    public void cliDownloadLog(OutputStream out) throws IOException {
        _outgoing.printf("log\n");
        Event.Base bevent = nextEvent(out);
        if (bevent instanceof Event.DisplayMultiString) {
        }
        else {
            throw new SoftError(
                String.format(
                    "Unexpected event %s",
                    bevent
                )
            );
        }
    }

    /**
     * noop command.
     */
    public void cliNoop() throws IOException {
        _outgoing.printf("noop\n");
    }

    /**
     * quit command.
     */
    public void cliQuit() throws IOException {
        _outgoing.printf("quit\n");
    }

    /**
     * install command.
     */
    public void cliInstall() throws IOException {
        _outgoing.printf("install\n");
    }

    /**
     * abort command.
     */
    public void cliAbort() throws IOException {
        _outgoing.printf("abort\n");
    }

    /**
     * Get next event from stream.
     * @param out output stream for multistring display.
     * @return Next event in stream.
     */
    public Event.Base nextEvent(OutputStream out) throws IOException, SoftError {
        Event.Base bevent = null;
        String line;

        while (
            bevent == null &&
            _incoming != null &&
            (line = _incoming.readLine()) != null
        ) {
            try{
                log.debug(String.format("Got: %1$s", line));

                if (line.startsWith(DialogMachineConst.NOTE_PREFIX)) {
                }
                else if (line.startsWith(DialogMachineConst.REQUEST_PREFIX)) {
                    bevent = _parseRequest(
                        line.substring(DialogMachineConst.REQUEST_PREFIX.length()),
                        out
                    );
                }
                else {
                    throw new RuntimeException("Invalid data recieved during bootstrap");
                }
            }
            catch (IOException e) {
                log.error("Cannot parse input", e);
                throw e;
            }
            catch (RuntimeException e) {
                log.error("Cannot parse input", e);
                throw e;
            }
            catch (Exception e) {
                log.error("Cannot parse input", e);
                throw new IOException("Cannot parse input", e);
            }
        }

        if (bevent == null) {
            throw new IOException("Unexpected connection termination");
        }

        log.debug(
            String.format(
                "nextEvent: %s",
                bevent
            )
        );
        return bevent;
    }

    /**
     * Get next event from stream.
     * @return Next event in stream.
     */
    public Event.Base nextEvent() throws IOException {
        return nextEvent(null);
    }

    /**
     * Send response of an event.
     * @param bevent event that holds the response.
     */
    public void sendResponse(Event.Base bevent) {
        if (bevent instanceof Event.QueryString) {
            Event.QueryString event = (Event.QueryString)bevent;
            if (event.value == null) {
                throw new IllegalArgumentException("value cannot be null");
            }
            if (event.value.indexOf("\n") != -1) {
                throw new IllegalArgumentException("value cannot contain new line");
            }
            _outgoing.println(event.value);
        }
        else if (bevent instanceof Event.QueryMultiString) {
            Event.QueryMultiString event = (Event.QueryMultiString)bevent;
            if (event.abort) {
                _outgoing.println(event.abortboundary);
            }
            else {
                if (event.value == null) {
                    throw new IllegalArgumentException("value cannot be null");
                }
                for (String s : event.value) {
                    _outgoing.println(s);
                }
                _outgoing.println(event.boundary);
            }
        }
        else if (bevent instanceof Event.QueryValue) {
            Event.QueryValue event = (Event.QueryValue)bevent;

            String type;
            if (event.value == null) {
                type = Types.NONE;
            }
            else if (event.value instanceof Boolean) {
                type = Types.BOOLEAN;
            }
            else if (event.value instanceof Integer) {
                type = Types.INTEGER;
            }
            else if (event.value instanceof String) {
                type = Types.STRING;

                if (((String)event.value).indexOf("\n") != -1) {
                    throw new IllegalArgumentException(
                        String.format(
                            "String '%s' should not contain new lines",
                            event.name
                        )
                    );
                }
            }
            else {
                throw new IllegalArgumentException(
                    String.format(
                        "Invalid type %s",
                        event.value.getClass().getName()
                    )
                );
            }

            if (event.abort) {
                _outgoing.printf(
                    "%s %s\n",
                    DialogMachineConst.QUERY_VALUE_RESPONSE_ABORT,
                    event.name
                );
            }
            else {
                _outgoing.printf(
                    "%s %s=%s:%s\n",
                    DialogMachineConst.QUERY_VALUE_RESPONSE_VALUE,
                    event.name,
                    type,
                    event.value
                );
            }
        }
        else if (bevent instanceof Event.Confirm) {
            Event.Confirm event = (Event.Confirm)bevent;
            if (event.abort) {
                _outgoing.printf(
                    "%s %s\n",
                    DialogMachineConst.CONFIRM_RESPONSE_ABORT,
                    event.what
                );
            }
            else {
                _outgoing.printf(
                    "%s %s=%s\n",
                    DialogMachineConst.CONFIRM_RESPONSE_VALUE,
                    event.what,
                    event.reply ? "yes" : "no"
                );
            }
        }
        else {
            // no response required.
        }
    }
}
