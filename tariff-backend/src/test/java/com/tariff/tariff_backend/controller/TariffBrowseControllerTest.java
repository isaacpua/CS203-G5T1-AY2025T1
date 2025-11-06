package com.tariff.tariff_backend.controller;

import com.tariff.tariff_backend.config.ApplicationConfig;
import com.tariff.tariff_backend.config.CorsConfig;
import com.tariff.tariff_backend.config.SecurityConfiguration;
import com.tariff.tariff_backend.model.tariffs_new.Tariff;
import com.tariff.tariff_backend.repository.TariffRepo;
import com.tariff.tariff_backend.security.JwtAuthenticationEntryPoint;
import com.tariff.tariff_backend.security.JwtAuthenticationFilter;
import com.tariff.tariff_backend.service.CalculationService;
import com.tariff.tariff_backend.service.CalculatorHistoryService;
import com.tariff.tariff_backend.service.JwtService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Collections;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(TariffBrowseController.class)
@Import({
    SecurityConfiguration.class, 
    CorsConfig.class,
    JwtAuthenticationEntryPoint.class,  // <-- ADD THIS
    JwtAuthenticationFilter.class       // <-- ADD THIS
})
public class TariffBrowseControllerTest {

    @Autowired
    private MockMvc mockMvc;

    // FIX: Mock all controller dependencies
    @MockBean
    private TariffRepo repo;

    @MockBean
    private CalculationService calcService;

    @MockBean
    private CalculatorHistoryService calcHistService;

    // Mocks required by SecurityConfiguration
    @MockBean
    private JwtService jwtService;

    @MockBean
    private ApplicationConfig applicationConfig;


    @Test
    @WithMockUser
    public void testGetPartnerCountries() throws Exception {
        when(repo.availableFrom()).thenReturn(Collections.emptyList());

        mockMvc.perform(get("/api/v1/tariffs/countries/partners"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isArray());
    }

    @Test
    @WithMockUser
    public void testGetReporterCountries() throws Exception {
        when(repo.availableTo(any())).thenReturn(Collections.emptyList());

        mockMvc.perform(get("/api/v1/tariffs/countries/reporters")
                        .param("fromId", "123"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isArray());
    }

    @Test
    @WithMockUser
    public void testSearch() throws Exception {
        // FIX: Mock the repo.searchNative(...) call
        Tariff mockTariff = new Tariff();
        Page<Tariff> resultPage = new PageImpl<>(Collections.singletonList(mockTariff), Pageable.ofSize(10), 1);

        // FIX: Match the repo.searchNative signature
        when(repo.searchNative(
                eq(156), eq(840), eq("wheat"), eq(2020), eq(2023), any(Pageable.class)
        )).thenReturn(resultPage);

        mockMvc.perform(get("/api/v1/tariffs/search")
                        .param("fromId", "156")
                        .param("toId", "840")
                        .param("q", "wheat")
                        .param("yearFrom", "2020")
                        .param("yearTo", "2023")
                        .param("page", "0")
                        .param("size", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(1));
    }
}