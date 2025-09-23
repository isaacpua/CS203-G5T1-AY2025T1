package com.tariff.tariff_backend.controller;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.core.env.Environment;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/internal")
public class DevController {

    private final JdbcTemplate jdbc;
    private final Environment env;

    public DevController(JdbcTemplate jdbc, Environment env) {
        this.jdbc = jdbc;
        this.env = env;
    }

    @GetMapping("/db-info")
    public Map<String, Object> dbInfo() {
        Map<String, Object> out = new HashMap<>();

        // Masked DB_URL
        String dbUrl = System.getProperty("DB_URL");
        if (dbUrl == null || dbUrl.isBlank()) dbUrl = System.getenv("DB_URL");
        out.put("dbUrl", mask(dbUrl));

        // Masked JWT_SECRET (sanity)
        String jwt = System.getProperty("JWT_SECRET");
        if (jwt == null || jwt.isBlank()) jwt = System.getenv("JWT_SECRET");
        out.put("jwtSecretMasked", mask(jwt));

        // current schema / search_path
        try {
            String currentSchema = jdbc.queryForObject("select current_schema()", String.class);
            out.put("current_schema", currentSchema);
        } catch (Exception e) {
            out.put("current_schema_error", e.getMessage());
        }

        try {
            String searchPath = jdbc.queryForObject("show search_path", String.class);
            out.put("search_path", searchPath);
        } catch (Exception e) {
            // fallback
            out.put("search_path_error", e.getMessage());
        }

        // count in tariffs schema
        try {
            Integer cnt = jdbc.queryForObject("select count(*) from tariffs.tariff_new", Integer.class);
            out.put("count_tariffs_tariff_new", cnt);
        } catch (Exception e) {
            out.put("count_tariffs_tariff_new_error", e.getMessage());
        }

        // count in public schema
        try {
            Integer cnt2 = jdbc.queryForObject("select count(*) from public.tariff_new", Integer.class);
            out.put("count_public_tariff_new", cnt2);
        } catch (Exception e) {
            out.put("count_public_tariff_new_error", e.getMessage());
        }

        // list matching tables
        try {
            List<String> tables = jdbc.queryForList("select table_schema || '.' || table_name from information_schema.tables where table_name ilike '%tariff%'", String.class);
            out.put("matching_tables", tables);
        } catch (Exception e) {
            out.put("matching_tables_error", e.getMessage());
        }

        // configured default schema from properties
        String defaultSchema = env.getProperty("spring.jpa.properties.hibernate.default_schema");
        out.put("configured_default_schema", defaultSchema);

        return out;
    }

    private String mask(String s) {
        if (s == null) return null;
        if (s.length() <= 10) return "<short>";
        return s.substring(0, 6) + "..." + s.substring(s.length() - 4);
    }
}
