package com.tariff.tariff_backend.repository;

import com.tariff.tariff_backend.model.tariffs_new.Tariff;
import com.tariff.tariff_backend.dto.CountryDTO;
import com.tariff.tariff_backend.model.tariffs_new.Country;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

public interface TariffRepo extends JpaRepository<Tariff, Integer> {

    Optional<Tariff> findByTariffId(Integer tariffId);

    List<Tariff> findByDescriptionwcountry(String descriptionwcountry);

    List<Tariff> findByPartnerCountry(Country partnerCountry);

    List<Tariff> findByReporterCountry(Country reporterCountry);

    List<Tariff> findByUnitname(String unitname);

    List<Tariff> findByCategory(String category);

    List<Tariff> findByAdValorem(BigDecimal adValorem);

    List<Tariff> findBySpecificPerUnit(BigDecimal specificPerUnit);

    // Partial search
    List<Tariff> findByDescriptionwcountryContainingIgnoreCase(String keyword);
    // ---------- SEARCH (filters: FROM=partnercountry, TO=reportercountry, free text on description or id)
  @Query(
      value = """
              select *
              from tariffs.tariff_new t
              where (:fromId is null or t.partnercountry = :fromId)
                and (:toId   is null or t.reportercountry = :toId)
                and (
                      :q is null
                   or lower(t.descriptionwcountry) like lower(concat('%', :q, '%'))
                   or cast(t.tariffid as text) like concat('%', :q, '%')
                )
              order by t.tariffid
              """,
      countQuery = """
              select count(*)
              from tariffs.tariff_new t
              where (:fromId is null or t.partnercountry = :fromId)
                and (:toId   is null or t.reportercountry = :toId)
                and (
                      :q is null
                   or lower(t.descriptionwcountry) like lower(concat('%', :q, '%'))
                   or cast(t.tariffid as text) like concat('%', :q, '%')
                )
              """,
      nativeQuery = true
  )
  Page<Tariff> searchNative(
      @Param("fromId") Integer fromId,
      @Param("toId") Integer toId,
      @Param("q") String q,
      Pageable pageable
  );

  // ---------- DROPDOWNS (only countries that exist in tariffs)

  // FROM countries = distinct partnercountry present in tariffs
  @Query(
      value = """
              select distinct c.countryid as id, c.iso2, c.name
              from tariffs.tariff_new t
              join tariffs.country c on c.countryid = t.partnercountry
              order by c.name
              """,
      nativeQuery = true
  )
  List<Object[]> availableFromRaw();

  // TO countries = distinct reportercountry, optionally filtered by chosen FROM
  @Query(
      value = """
              select distinct c.countryid as id, c.iso2, c.name
              from tariffs.tariff_new t
              join tariffs.country c on c.countryid = t.reportercountry
              where (:fromId is null or t.partnercountry = :fromId)
              order by c.name
              """,
      nativeQuery = true
  )
  List<Object[]> availableToRaw(@Param("fromId") Integer fromId);

  // Convenience default mappers to CountryDTO
  default List<CountryDTO> availableFrom() {
    return availableFromRaw().stream()
        .map(a -> new CountryDTO(((Number)a[0]).intValue(), (String)a[1], (String)a[2]))
        .toList();
  }

  default List<CountryDTO> availableTo(Integer fromId) {
    return availableToRaw(fromId).stream()
        .map(a -> new CountryDTO(((Number)a[0]).intValue(), (String)a[1], (String)a[2]))
        .toList();
  }
}
