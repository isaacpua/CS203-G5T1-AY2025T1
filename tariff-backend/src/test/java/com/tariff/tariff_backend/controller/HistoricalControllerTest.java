// src/test/java/com/tariff/tariff_backend/controller/HistoricalControllerTest.java
package com.tariff.tariff_backend.controller;

import com.tariff.tariff_backend.config.ApplicationConfig;
import com.tariff.tariff_backend.config.CorsConfig;
import com.tariff.tariff_backend.config.SecurityConfiguration;
import com.tariff.tariff_backend.model.history.HistoricalResponse;
import com.tariff.tariff_backend.model.history.HistoryPreset;
import com.tariff.tariff_backend.model.history.Unit;
import com.tariff.tariff_backend.security.JwtAuthenticationEntryPoint;
import com.tariff.tariff_backend.security.JwtAuthenticationFilter;
import com.tariff.tariff_backend.service.HistoricalService;
import com.tariff.tariff_backend.service.JwtService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDate;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(HistoricalController.class)
@Import({
    SecurityConfiguration.class,
    CorsConfig.class,
    JwtAuthenticationEntryPoint.class,
    JwtAuthenticationFilter.class
})
class HistoricalControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private HistoricalService historicalService;

    // Mocks required by SecurityConfiguration
    @MockBean
    private JwtService jwtService;
    @MockBean
    private ApplicationConfig applicationConfig;

    @Test
    @WithMockUser // This endpoint is secured, so we need a mock user
    public void testGetHistory_WithParams() throws Exception {
        HistoricalResponse mockResponse = new HistoricalResponse();
        mockResponse.setReporter("USA");
        mockResponse.setPartner("CHN");

        when(historicalService.getHistory(
                eq("USA"), eq("CHN"), eq("123"),
                any(LocalDate.class), any(LocalDate.class), eq(Unit.VALUE)
        )).thenReturn(mockResponse);

        mockMvc.perform(get("/api/v1/tariffs/history")
                        .param("reporter", "USA")
                        .param("partner", "CHN")
                        .param("itemCode", "123")
                        .param("start", "2023-01-01")
                        .param("end", "2024-01-01")
                        .param("unit", "value"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.reporter").value("USA"));
    }

    @Test
    @WithMockUser
    public void testGetHistory_WithDefaults() throws Exception {
        HistoricalResponse mockResponse = new HistoricalResponse();
        mockResponse.setUnit(Unit.PERCENT);

        when(historicalService.getHistory(
                eq(null), eq(null), eq(null),
                eq(null), eq(null), eq(Unit.PERCENT)
        )).thenReturn(mockResponse);

        mockMvc.perform(get("/api/v1/tariffs/history"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.unit").value("PERCENT"));
    }

    @Test
    @WithMockUser
    public void testGetRecommendations() throws Exception {
        HistoryPreset preset = new HistoryPreset("Test Preset", "R", "P", "1");
        when(historicalService.presets()).thenReturn(List.of(preset));

        mockMvc.perform(get("/api/v1/tariffs/recommendations"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].title").value("Test Preset"));
    }
}