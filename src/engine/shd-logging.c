/*
 * The Shadow Simulator
 *
 * Copyright (c) 2010-2011 Rob Jansen <jansen@cs.umn.edu>
 *
 * This file is part of Shadow.
 *
 * Shadow is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Shadow is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Shadow.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "shadow.h"

static gchar* _logging_getLogLevelString(GLogLevelFlags log_level) {
	gchar* levels;
	switch (log_level) {
		case G_LOG_LEVEL_ERROR: {
			levels = "error";
			break;
		}
		case G_LOG_LEVEL_CRITICAL: {
			levels = "critical";
			break;
		}

		case G_LOG_LEVEL_WARNING: {
			levels = "warning";
			break;
		}

		case G_LOG_LEVEL_MESSAGE: {
			levels = "message";
			break;
		}

		case G_LOG_LEVEL_INFO: {
			levels = "info";
			break;
		}

		case G_LOG_LEVEL_DEBUG: {
			levels = "debug";
			break;
		}

		default: {
			levels = "default";
			break;
		}
	}
	return levels;
}

static const gchar* _logging_getLogDomainString(const gchar *log_domain) {
	const gchar* domains = log_domain != NULL ? log_domain : "shadow";
	return domains;
}

void logging_handleLog(const gchar *log_domain, GLogLevelFlags log_level, const gchar *message, gpointer user_data) {
	GLogLevelFlags* configuredLogLevel = user_data;
	if(log_level > *configuredLogLevel) {
		return;
	}

	/* callback from GLib, no access to workers */
	GDateTime* dt_now = g_date_time_new_now_local();
	gchar* dt_format = g_date_time_format(dt_now, "%F %H:%M:%S:%N");

	g_print("%s %s\n", dt_format, message);

	g_date_time_unref(dt_now);
	g_free(dt_format);

	if(log_level & G_LOG_LEVEL_ERROR) {
		g_print("\t**aborting**\n");
	}
}

void logging_logv(const gchar *log_domain, GLogLevelFlags log_level, const gchar* functionName, const gchar *format, va_list vargs) {
	/* this is called by worker threads, so we have access to worker */
	Worker* w = worker_getPrivate();

	/* format the simulation time if we are running an event */
	GString* simtime = NULL;
	if(w->clock_now != SIMTIME_INVALID) {
		SimulationTime hours, minutes, seconds, remainder;
		remainder = w->clock_now;

		hours = remainder / SIMTIME_ONE_HOUR;
		remainder %= SIMTIME_ONE_HOUR;
		minutes = remainder / SIMTIME_ONE_MINUTE;
		remainder %= SIMTIME_ONE_MINUTE;
		seconds = remainder / SIMTIME_ONE_SECOND;
		remainder %= SIMTIME_ONE_SECOND;

		simtime = g_string_new("");
		g_string_append_printf(simtime, "%lu:%lu:%lu:%lu", hours, minutes, seconds, remainder);
	}

	/* the time - we'll need to free clockString later */
	gchar* clockString = !simtime ? g_strdup("n/a") : g_string_free(simtime, FALSE);

	/* node identifier, if we are running a node
	 * dont free this since we dont own the ip address string */
	const gchar* nodeString = !w->cached_node ? "n/a" :
			address_toHostName(w->cached_node->address);

	/* the function name - no need to free this */
	const gchar* functionString = !functionName ? "n/a" : functionName;

	GString* newLogFormatBuffer = g_string_new(NULL);
	g_string_printf(newLogFormatBuffer, "[thread-%i] %s [%s-%s] [%s] [%s] %s",
			w->thread_id,
			clockString,
			_logging_getLogDomainString(log_domain),
			_logging_getLogLevelString(log_level),
			nodeString,
			functionString,
			format
			);

	/* get the new format out of our string buffer and log it */
	gchar* newLogFormat = g_string_free(newLogFormatBuffer, FALSE);
	g_logv(log_domain, log_level, newLogFormat, vargs);

	/* cleanup */
	g_free(newLogFormat);
	g_free(clockString);
}

void logging_log(const gchar *log_domain, GLogLevelFlags log_level, const gchar* functionName, const gchar *format, ...) {
	va_list vargs;
	va_start(vargs, format);

	logging_logv(log_domain, log_level, functionName, format, vargs);

	va_end(vargs);
}